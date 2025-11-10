"""Service for handling assessment-related operations."""

import logging
from fastapi import Depends
from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from app.exceptions import (
    AppException,
    AssessmentNotFoundException,
    CourseNotFoundException,
    SemesterNotFoundException
)

from app.db import get_db
from app.models.course import Course
from app.models.course_in_semester import CourseInSemester
from app.models.semester import Semester
from app.models.assessment import Assessment
from app.models.statistics import Statistics
from app.schemas.assessment import AssessmentCreate, AssessmentUpdate

logger = logging.getLogger(__name__)

class AssessmentService:
    """Service class for assessment operations."""
    def __init__(self, db: Session = Depends(get_db)):
        """Initialize the service with a database session."""
        self.db = db

    def get_all_assessments(self, semester_id: int, course_id: int, user_id: str):
        """Retrieve all assessments for a specific course in semester,
        only if it belongs to the user.
        """
        return (
            self.db.query(Assessment)
            .join(CourseInSemester,
                and_(
                    Assessment.id_course == CourseInSemester.Course_id_course,
                    Assessment.id_semester == CourseInSemester.Semester_id_semester
                )
            )
            .join(Course, CourseInSemester.Course_id_course == Course.id_course)
            .join(Semester, CourseInSemester.Semester_id_semester == Semester.id_semester)
            .filter(
                Course.id_user == user_id,
                Semester.id_user == user_id,
                Assessment.id_course == course_id,
                Assessment.id_semester == semester_id,
                Assessment.is_deleted.is_(False)
            )
            .all()
        )

    def get_assessment(self, assessment_id: int, user_id: str):
        """Retrieve a specific assessment by its ID, only if it belongs to the user."""
        db_assessment = (
            self.db.query(Assessment)
            .join(CourseInSemester,
                and_(
                    Assessment.id_course == CourseInSemester.Course_id_course,
                    Assessment.id_semester == CourseInSemester.Semester_id_semester
                )
            )
            .join(Course, CourseInSemester.Course_id_course == Course.id_course)
            .join(Semester, CourseInSemester.Semester_id_semester == Semester.id_semester)
            .filter(
                Assessment.id_assessment == assessment_id,
                Course.id_user == user_id,
                Semester.id_user == user_id,
                Assessment.is_deleted.is_(False)
            )
            .first()
        )

        if not db_assessment:
            logger.warning("Assessment with id %s not found for user %s.",
                           assessment_id, user_id)
            raise AssessmentNotFoundException()
        return db_assessment

    def create_assessment(self, assessment: AssessmentCreate, user_id: str):
        """Create a new assessment in the database,
        only if the course and semester belong to the user.
        """
        course = self.db.query(Course).filter(
            Course.id_course == assessment.id_course,
            Course.id_user == user_id
        ).first()
        if not course:
            logger.warning("Course not found for course_id %s and user_id %s.",
                           assessment.id_course, user_id)
            raise CourseNotFoundException()

        semester = self.db.query(Semester).filter(
            Semester.id_semester == assessment.id_semester,
            Semester.id_user == user_id
        ).first()
        if not semester:
            logger.warning("Semester not found for semester_id %s and user_id %s.",
                           assessment.id_semester, user_id)
            raise SemesterNotFoundException()

        assessment_data = assessment.model_dump()
        db_assessment = Assessment(**assessment_data)

        try:
            self.db.add(db_assessment)
            self.db.commit()
            self.db.refresh(db_assessment)
            return db_assessment
        except IntegrityError as e:
            self.db.rollback()
            logger.error("Integrity error while creating assessment for user %s: %s",
                         user_id, e, exc_info=True)
            raise AppException() from e

    def update_assessment(self, assessment_id: int,
                          user_id: str, updated_assessment: AssessmentUpdate):
        """Update an existing assessment in the database."""
        db_assessment = self.get_assessment(assessment_id, user_id)
        update_data = updated_assessment.model_dump()

        for key, value in update_data.items():
            setattr(db_assessment, key, value)

        try:
            self.db.commit()
            self.db.refresh(db_assessment)
            logger.info("Assessment with id %s updated for user %s.",
                        assessment_id, user_id)
            return db_assessment
        except IntegrityError as e:
            self.db.rollback()
            logger.error("Integrity error while updating assessment %s for user %s: %s",
                         assessment_id, user_id, e, exc_info=True)
            raise AppException() from e

    def delete_assessment(self, assessment_id: int, user_id: str):
        """Soft delete an assessment from the database."""
        db_assessment = self.get_assessment(assessment_id, user_id)

        try:
            # Soft delete associated statistics
            self.db.query(Statistics).filter(
                Statistics.id_assessment == assessment_id,
                Statistics.is_deleted.is_(False)
            ).update(
                {
                    Statistics.is_deleted: True,
                    Statistics.deleted_at: func.now()
                },
                synchronize_session=False
            )

            # Soft delete the assessment
            db_assessment.is_deleted = True
            db_assessment.deleted_at = func.now()

            self.db.commit()
            self.db.refresh(db_assessment)
            logger.info("Assessment with id %s soft deleted for user %s.",
                        assessment_id, user_id)
            return db_assessment
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error("Error occurred while soft deleting assessment %s for user %s: %s",
                         assessment_id, user_id, e, exc_info=True)
            raise AppException() from e
