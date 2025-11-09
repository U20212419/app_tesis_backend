"""Service for handling course-related operations."""

import logging
from fastapi import Depends
from sqlalchemy import and_, or_
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from app.exceptions import (
    AppException,
    CourseNotFoundException,
    CourseCodeDuplicateException
)

from app.db import get_db
from app.models.assessment import Assessment
from app.models.course import Course
from app.models.course_in_semester import CourseInSemester
from app.models.section import Section
from app.models.statistics import Statistics
from app.schemas.course import CourseCreate

logger = logging.getLogger(__name__)

class CourseService:
    """Service class for course operations."""
    def __init__(self, db: Session = Depends(get_db)):
        """Initialize the service with a database session."""
        self.db = db

    def get_all_courses(self, user_id: str):
        """Retrieve all courses for a specific user."""
        return self.db.query(Course).filter(
                Course.id_user == user_id,
                Course.is_deleted.is_(False)
            ).all()

    def get_course(self, course_id: int, user_id: str):
        """Retrieve a specific course by its ID, only if it belongs to the user."""
        db_course = self.db.query(Course).filter(
                Course.id_course == course_id,
                Course.id_user == user_id,
                Course.is_deleted.is_(False)
            ).first()

        if not db_course:
            logger.warning("Course with id %s not found for user %s.",
                           course_id, user_id)
            raise CourseNotFoundException()
        return db_course

    def create_course(self, course: CourseCreate, user_id: str):
        """Create a new course in the database."""
        course_data = course.model_dump()
        db_course = Course(
            **course_data,
            id_user=user_id,
            active_code=course_data['code']
        )

        try:
            self.db.add(db_course)
            self.db.commit()
            self.db.refresh(db_course)
            db_course.semester_count = 0
            logger.info("Course '%s' created for user %s.",
                        course_data['code'], user_id)
            return db_course
        except IntegrityError as e:
            self.db.rollback()
            db_error_code = e.orig.args[0] if e.orig and hasattr(e.orig, 'args') else 0

            if db_error_code == 1062:  # MySQL duplicate entry error code
                logger.warning("Duplicate course code '%s' for user %s when creating.",
                               course_data['code'], user_id)
                raise CourseCodeDuplicateException() from e

            logger.error("Integrity error while creating course for user %s: %s",
                            user_id, e, exc_info=True)
            raise AppException() from e

    def get_all_courses_detailed(self, user_id: str):
        """Retrieve all courses for a specific user,
        including the amount of semesters in which each course is present.
        """
        results = (
            self.db.query(
                Course,
                func.count(CourseInSemester.Semester_id_semester).label("semester_count")
            )
            .outerjoin(
                CourseInSemester,
                and_(
                    Course.id_course == CourseInSemester.Course_id_course,
                    CourseInSemester.is_deleted.is_(False)
                )
            )
            .filter(
                Course.id_user == user_id,
                Course.is_deleted.is_(False)
            )
            .group_by(Course.id_course)
            .all()
        )

        return [
            (setattr(course, "semester_count", semester_count or 0) or course)
            for course, semester_count in results
        ]

    def update_course(self, course_id: int, user_id: str, updated_course: CourseCreate):
        """Update an existing course in the database."""
        db_course = self.get_course(course_id, user_id)
        update_data = updated_course.model_dump()

        for key, value in update_data.items():
            setattr(db_course, key, value)
        if 'code' in update_data:
            db_course.active_code = update_data['code']

        try:
            self.db.commit()
            self.db.refresh(db_course)
            logger.info("Course with id %s updated for user %s.",
                        course_id, user_id)
            return db_course
        except IntegrityError as e:
            self.db.rollback()
            db_error_code = e.orig.args[0] if e.orig and hasattr(e.orig, 'args') else 0

            if db_error_code == 1062:  # MySQL duplicate entry error code
                logger.warning("Duplicate course code '%s' for user %s when updating.",
                               update_data['code'], user_id)
                raise CourseCodeDuplicateException() from e

            logger.error("Integrity error while updating course %s for user %s: %s",
                            course_id, user_id, e, exc_info=True)
            raise AppException() from e

    def delete_course(self, course_id: int, user_id: str):
        """Soft delete a course from the database."""
        db_course = self.get_course(course_id, user_id)

        try:
            assessment_id_tuples = (
                self.db.query(Assessment.id_assessment)
                .filter(
                    Assessment.id_course == course_id,
                    Assessment.is_deleted.is_(False)
                )
            ).all()

            assessment_ids_to_delete = [item[0] for item in assessment_id_tuples]

            section_id_tuples = (
                self.db.query(Section.id_section)
                .filter(
                    Section.id_course == course_id,
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
                CourseInSemester.Course_id_course == course_id,
                CourseInSemester.is_deleted.is_(False)
            ).update(
                {
                    CourseInSemester.is_deleted: True,
                    CourseInSemester.deleted_at: func.now()
                },
                synchronize_session=False
            )

            #Soft delete the course
            db_course.is_deleted = True
            db_course.deleted_at = func.now()
            db_course.active_code = None

            self.db.commit()
            self.db.refresh(db_course)
            logger.info("Course with id %s soft deleted for user %s.", course_id, user_id)
            return db_course
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error("Error while soft deleting course %s for user %s: %s",
                         course_id, user_id, e, exc_info=True)
            raise AppException() from e
