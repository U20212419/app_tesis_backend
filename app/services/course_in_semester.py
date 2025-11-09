"""Service for handling course-in-semester-related operations."""

import logging
from fastapi import Depends
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import joinedload, Session
from sqlalchemy.sql import func

from app.exceptions import (
    AppException,
    CourseNotFoundException,
    SemesterNotFoundException,
    CourseInSemesterNotFoundException,
    CourseAlreadyInSemesterException
)

from app.db import get_db
from app.models.assessment import Assessment
from app.models.course import Course
from app.models.section import Section
from app.models.semester import Semester
from app.models.course_in_semester import CourseInSemester
from app.models.statistics import Statistics

logger = logging.getLogger(__name__)

class CourseInSemesterService:
    """Service class for course in semester operations."""
    def __init__(self, db: Session = Depends(get_db)):
        """Initialize the service with a database session."""
        self.db = db

    def get_all_courses_in_semesters(self, user_id: str):
        """Retrieve all courses in all semesters, only if they belong to the user."""
        return (
            self.db.query(CourseInSemester)
            .options(
                joinedload(CourseInSemester.course)
            )
            .join(Course, CourseInSemester.Course_id_course == Course.id_course)
            .join(Semester, CourseInSemester.Semester_id_semester == Semester.id_semester)
            .filter(
                CourseInSemester.is_deleted.is_(False),
                Course.id_user == user_id,
                Course.is_deleted.is_(False),
                Semester.id_user == user_id,
                Semester.is_deleted.is_(False)
            )
            .all()
        )

    def get_all_courses_in_semester(self, semester_id: int, user_id: str):
        """Retrieve all courses in a specific semester, only if they belong to the user."""
        # Assessment count subquery
        assessment_subq = (
            self.db.query(
                Assessment.id_course,
                func.count(Assessment.id_assessment).label("assessment_count")
            )
            .filter(
                Assessment.id_semester == semester_id,
                Assessment.is_deleted.is_(False)
            )
            .group_by(Assessment.id_course)
            .subquery()
        )

        # Section count subquery
        section_subq = (
            self.db.query(
                Section.id_course,
                func.count(Section.id_section).label("section_count")
            )
            .filter(
                Section.id_semester == semester_id,
                Section.is_deleted.is_(False)
            )
            .group_by(Section.id_course)
            .subquery()
        )

        # Main query
        results = (
            self.db.query(
                CourseInSemester,
                assessment_subq.c.assessment_count,
                section_subq.c.section_count
            )
            .options(
                joinedload(CourseInSemester.course)
            )
            .join(Course, CourseInSemester.Course_id_course == Course.id_course)
            .join(Semester, CourseInSemester.Semester_id_semester == Semester.id_semester)
            .outerjoin(
                assessment_subq,
                CourseInSemester.Course_id_course == assessment_subq.c.id_course
            )
            .outerjoin(
                section_subq,
                CourseInSemester.Course_id_course == section_subq.c.id_course
            )
            .filter(
                CourseInSemester.is_deleted.is_(False),
                Course.id_user == user_id,
                Course.is_deleted.is_(False),
                Semester.id_user == user_id,
                Semester.is_deleted.is_(False),
                Semester.id_semester == semester_id
            )
            .all()
        )

        final_results = []
        for course_in_semester, assessment_count, section_count in results:
            course_in_semester.assessment_count = assessment_count or 0
            course_in_semester.section_count = section_count or 0
            final_results.append(course_in_semester)

        return final_results

    def get_course_in_semester(self, semester_id: int, course_id: int, user_id: str):
        """Retrieve a specific course in a semester by their IDs,
        only if they belong to the user.
        """
        # Assessment count subquery
        assessment_subq = (
            self.db.query(
                Assessment.id_course,
                func.count(Assessment.id_assessment).label("assessment_count")
            )
            .filter(
                Assessment.id_semester == semester_id,
                Assessment.is_deleted.is_(False)
            )
            .group_by(Assessment.id_course)
            .subquery()
        )

        # Section count subquery
        section_subq = (
            self.db.query(
                Section.id_course,
                func.count(Section.id_section).label("section_count")
            )
            .filter(
                Section.id_semester == semester_id,
                Section.is_deleted.is_(False)
            )
            .group_by(Section.id_course)
            .subquery()
        )

        # Main query
        result = (
            self.db.query(
                CourseInSemester,
                assessment_subq.c.assessment_count,
                section_subq.c.section_count
            )
            .options(
                joinedload(CourseInSemester.course)
            )
            .join(Course, CourseInSemester.Course_id_course == Course.id_course)
            .join(Semester, CourseInSemester.Semester_id_semester == Semester.id_semester)
            .outerjoin(
                assessment_subq,
                CourseInSemester.Course_id_course == assessment_subq.c.id_course
            )
            .outerjoin(
                section_subq,
                CourseInSemester.Course_id_course == section_subq.c.id_course
            )
            .filter(
                CourseInSemester.Course_id_course == course_id,
                CourseInSemester.Semester_id_semester == semester_id,
                CourseInSemester.is_deleted.is_(False),
                Course.id_user == user_id,
                Course.is_deleted.is_(False),
                Semester.id_user == user_id,
                Semester.is_deleted.is_(False)
            )
            .first()
        )

        if not result:
            logger.warning("CourseInSemester not found for "
                           "course_id %s and semester_id %s for user %s.",
                           course_id, semester_id, user_id)
            raise CourseInSemesterNotFoundException()

        course_in_semester, assessment_count, section_count = result
        course_in_semester.assessment_count = assessment_count or 0
        course_in_semester.section_count = section_count or 0
        return course_in_semester

    def add_course_to_semester(self, semester_id: int, course_id: int, user_id: str):
        """Add a course to a semester in the database, only if they belong to the user."""
        course = self.db.query(Course).filter(
            Course.id_course == course_id,
            Course.id_user == user_id,
            Course.is_deleted.is_(False)
        ).first()
        if not course:
            logger.warning("Course not found for course_id %s and user_id %s.",
                           course_id, user_id)
            raise CourseNotFoundException()

        semester = self.db.query(Semester).filter(
            Semester.id_semester == semester_id,
            Semester.id_user == user_id,
            Semester.is_deleted.is_(False)
        ).first()
        if not semester:
            logger.warning("Semester not found for semester_id %s and user_id %s.",
                           semester_id, user_id)
            raise SemesterNotFoundException()

        # Searches for an existing CourseInSemester entry
        db_course_in_semester = self.db.query(CourseInSemester).filter(
            CourseInSemester.Course_id_course == course_id,
            CourseInSemester.Semester_id_semester == semester_id
        ).first()

        if db_course_in_semester:
            if db_course_in_semester.is_deleted is False:
                logger.warning("Course with id %s is already in semester %s for user %s.",
                               course_id, semester_id, user_id)
                raise CourseAlreadyInSemesterException()

            # If it exists and is deleted, reactivate it
            db_course_in_semester.is_deleted = False
            db_course_in_semester.deleted_at = None
        else:
            # Create a new CourseInSemester entry
            db_course_in_semester = CourseInSemester(
                Course_id_course=course_id,
                Semester_id_semester=semester_id
            )
            self.db.add(db_course_in_semester)

        try:
            self.db.commit()
            self.db.refresh(db_course_in_semester)
            logger.info("Course with id %s added to semester %s for user %s.",
                        course_id, semester_id, user_id)
            return db_course_in_semester
        except IntegrityError as e:
            self.db.rollback()
            logger.error("Integrity error while adding course %s to semester %s for user %s: %s",
                         course_id, semester_id, user_id, e, exc_info=True)
            raise AppException() from e

    def remove_course_from_semester(self, semester_id: int, course_id: int,
                                    user_id: str):
        """Remove a course from a semester in the database, only if they belong to the user.
        Its children entities are also soft deleted.
        """
        db_course_in_semester = self.get_course_in_semester(semester_id, course_id, user_id)

        try:
            assessment_id_tuples = (
                self.db.query(Assessment.id_assessment)
                .filter(
                    Assessment.id_semester == semester_id,
                    Assessment.id_course == course_id,
                    Assessment.is_deleted.is_(False)
                )
            ).all()

            assessment_ids_to_delete = [item[0] for item in assessment_id_tuples]

            section_id_tuples = (
                self.db.query(Section.id_section)
                .filter(
                    Section.id_semester == semester_id,
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

            # Soft delete the CourseInSemester entry
            db_course_in_semester.is_deleted = True
            db_course_in_semester.deleted_at = func.now()
            self.db.commit()
            self.db.refresh(db_course_in_semester)
            logger.info("Course with id %s removed from semester %s for user %s.",
                        course_id, semester_id, user_id)
            return db_course_in_semester
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error("Error while removing course %s from semester %s for user %s: %s",
                         course_id, semester_id, user_id, e, exc_info=True)
            raise AppException() from e
