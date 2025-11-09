"""Service for handling semester-related operations."""

import logging
from fastapi import Depends
from sqlalchemy import and_, or_
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from app.exceptions import (
    AppException,
    SemesterNotFoundException,
    SemesterKeyDuplicateException
)

from app.db import get_db
from app.models.assessment import Assessment
from app.models.course_in_semester import CourseInSemester
from app.models.section import Section
from app.models.semester import Semester
from app.models.statistics import Statistics
from app.schemas.semester import SemesterCreate

logger = logging.getLogger(__name__)

class SemesterService:
    """Service class for semester operations."""
    def __init__(self, db: Session = Depends(get_db)):
        """Initialize the service with a database session."""
        self.db = db

    def get_all_semesters(self, user_id: str):
        """Retrieve all semesters for a specific user."""
        return self.db.query(Semester).filter(
                Semester.id_user == user_id,
                Semester.is_deleted.is_(False)
            ).all()

    def get_semester(self, semester_id: int, user_id: str):
        """Retrieve a specific semester by its ID, only if it belongs to the user."""
        db_semester = self.db.query(Semester).filter(
                Semester.id_semester == semester_id,
                Semester.id_user == user_id,
                Semester.is_deleted.is_(False)
            ).first()

        if not db_semester:
            logger.warning("Semester with id %s not found for user %s.",
                           semester_id, user_id)
            raise SemesterNotFoundException()
        return db_semester

    def create_semester(self, semester: SemesterCreate, user_id: str):
        """Create a new semester in the database."""
        semester_data = semester.model_dump()
        semester_key = f"{semester_data['year']}-{semester_data['number']}"
        db_semester = Semester(
            **semester_data,
            id_user=user_id,
            active_semester_key=semester_key
        )

        try:
            self.db.add(db_semester)
            self.db.commit()
            self.db.refresh(db_semester)
            db_semester.courses_count = 0
            return db_semester
        except IntegrityError as e:
            self.db.rollback()
            error_info = str(e.orig).lower()

            if "duplicate entry" in error_info and "active_semester_key" in error_info:
                logger.warning("Duplicate semester key '%s' for user %s.",
                               semester_key, user_id)
                raise SemesterKeyDuplicateException() from e

            logger.error("Integrity error while creating semester for user %s: %s",
                         user_id, e, exc_info=True)
            raise AppException() from e

    def get_all_semesters_detailed(self, user_id: str):
        """Retrieve all semesters for a specific user,
        including the amount of courses that are present in each semester.
        """
        results = (
            self.db.query(
                Semester,
                func.count(CourseInSemester.Course_id_course).label("course_count")
            )
            .outerjoin(
                CourseInSemester,
                and_(
                    Semester.id_semester == CourseInSemester.Semester_id_semester,
                    CourseInSemester.is_deleted.is_(False)
                )
            )
            .filter(
                Semester.id_user == user_id,
                Semester.is_deleted.is_(False)
            )
            .group_by(Semester.id_semester)
            .all()
        )

        return [
            (setattr(semester, "course_count", course_count or 0) or semester)
            for semester, course_count in results
        ]

    def update_semester(self, semester_id: int, user_id: str, updated_semester: SemesterCreate):
        """Update an existing semester in the database."""
        db_semester = self.get_semester(semester_id, user_id)
        update_data = updated_semester.model_dump()
        for key, value in updated_semester.model_dump().items():
            setattr(db_semester, key, value)
        if 'year' in update_data or 'number' in update_data:
            semester_key = f"{db_semester.year}-{db_semester.number}"
            db_semester.active_semester_key = semester_key

        try:
            self.db.commit()
            self.db.refresh(db_semester)
            logger.info("Semester with id %s updated for user %s.",
                        semester_id, user_id)
            return db_semester
        except IntegrityError as e:
            self.db.rollback()
            error_info = str(e.orig).lower()

            if "duplicate entry" in error_info and "active_semester_key" in error_info:
                logger.warning("Duplicate semester key '%s' for user %s when updating.",
                               db_semester.active_semester_key, user_id)
                raise SemesterKeyDuplicateException() from e

            logger.error("Integrity error while updating semester %s for user %s: %s",
                         semester_id, user_id, e, exc_info=True)
            raise AppException() from e

    def delete_semester(self, semester_id: int, user_id: str):
        """Soft delete a semester from the database."""
        db_semester = self.get_semester(semester_id, user_id)
        if db_semester:
            try:
                assessment_id_tuples = (
                    self.db.query(Assessment.id_assessment)
                    .filter(
                        Assessment.id_semester == semester_id,
                        Assessment.is_deleted.is_(False)
                    )
                ).all()

                assessment_ids_to_delete = [item[0] for item in assessment_id_tuples]

                section_id_tuples = (
                    self.db.query(Section.id_section)
                    .filter(
                        Section.id_semester == semester_id,
                        Section.is_deleted.is_(False)
                    )
                ).all()

                section_ids_to_delete = [item[0] for item in section_id_tuples]

                # Soft delete associated statistics via cascade from Assessments and Sections
                self.db.query(Statistics).filter(
                    or_(
                        Statistics.id_assessment.in_(assessment_ids_to_delete),
                        Statistics.id_section.in_(section_ids_to_delete)
                    ),
                    Statistics.is_deleted.is_(False)
                ).update(
                    {
                        Statistics.is_deleted: True,
                        Statistics.deleted_at: func.now()
                    },
                    synchronize_session=False
                )

                # Soft delete associated Assessments and Sections
                self.db.query(Assessment).filter(
                    Assessment.id_assessment.in_(assessment_ids_to_delete)
                ).update(
                    {
                        Assessment.is_deleted: True,
                        Assessment.deleted_at: func.now()
                    },
                    synchronize_session=False
                )
                self.db.query(Section).filter(
                    Section.id_section.in_(section_ids_to_delete)
                ).update(
                    {
                        Section.is_deleted: True,
                        Section.deleted_at: func.now()
                    },
                    synchronize_session=False
                )

                # Soft delete associated CourseInSemester entries
                self.db.query(CourseInSemester).filter(
                    CourseInSemester.Semester_id_semester == semester_id,
                    CourseInSemester.is_deleted.is_(False)
                ).update(
                    {
                        CourseInSemester.is_deleted: True,
                        CourseInSemester.deleted_at: func.now()
                    },
                    synchronize_session=False
                )

                # Soft delete the semester
                db_semester.is_deleted = True
                db_semester.deleted_at = func.now()
                db_semester.active_semester_key = None

                self.db.commit()
                self.db.refresh(db_semester)
                logger.info("Semester with id %s soft deleted for user %s.",
                            semester_id, user_id)
                return db_semester
            except SQLAlchemyError as e:
                self.db.rollback()
                logger.error("Error occurred while soft deleting semester %s for user %s: %s",
                             semester_id, user_id, e)
                raise AppException() from e
