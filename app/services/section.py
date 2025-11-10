"""Service for handling section-related operations."""

import logging
from fastapi import Depends
from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from app.exceptions import (
    AppException,
    CourseNotFoundException,
    SectionNotFoundException,
    SemesterNotFoundException
)

from app.db import get_db
from app.models.course import Course
from app.models.course_in_semester import CourseInSemester
from app.models.semester import Semester
from app.models.section import Section
from app.models.statistics import Statistics
from app.schemas.section import SectionCreate, SectionUpdate

logger = logging.getLogger(__name__)

class SectionService:
    """Service class for section operations."""
    def __init__(self, db: Session = Depends(get_db)):
        """Initialize the service with a database session."""
        self.db = db

    def get_all_sections(self, semester_id: int, course_id: int, user_id: str):
        """Retrieve all sections for a specific course in semester,
        only if it belongs to the user.
        """
        return (
            self.db.query(Section)
            .join(CourseInSemester,
                and_(
                    Section.id_course == CourseInSemester.Course_id_course,
                    Section.id_semester == CourseInSemester.Semester_id_semester
                )
            )
            .join(Course, CourseInSemester.Course_id_course == Course.id_course)
            .join(Semester, CourseInSemester.Semester_id_semester == Semester.id_semester)
            .filter(
                Course.id_user == user_id,
                Semester.id_user == user_id,
                Section.id_course == course_id,
                Section.id_semester == semester_id,
                Section.is_deleted.is_(False)
            )
            .all()
        )

    def get_section(self, section_id: int, user_id: str):
        """Retrieve a specific section by its ID, only if it belongs to the user."""
        db_section = (
            self.db.query(Section)
            .join(CourseInSemester,
                and_(
                    Section.id_course == CourseInSemester.Course_id_course,
                    Section.id_semester == CourseInSemester.Semester_id_semester
                )
            )
            .join(Course, CourseInSemester.Course_id_course == Course.id_course)
            .join(Semester, CourseInSemester.Semester_id_semester == Semester.id_semester)
            .filter(
                Section.id_section == section_id,
                Course.id_user == user_id,
                Semester.id_user == user_id,
                Section.is_deleted.is_(False)
            )
            .first()
        )

        if not db_section:
            logger.warning("Section with id %s not found for user %s.",
                           section_id, user_id)
            raise SectionNotFoundException()
        return db_section

    def create_section(self, section: SectionCreate, user_id: str):
        """Create a new section in the database,
        only if the course and semester belong to the user.
        """
        course = self.db.query(Course).filter(
            Course.id_course == section.id_course,
            Course.id_user == user_id
        ).first()
        if not course:
            logger.warning("Course not found for course_id %s and user_id %s.",
                           section.id_course, user_id)
            raise CourseNotFoundException()

        semester = self.db.query(Semester).filter(
            Semester.id_semester == section.id_semester,
            Semester.id_user == user_id
        ).first()
        if not semester:
            logger.warning("Semester not found for semester_id %s and user_id %s.",
                           section.id_semester, user_id)
            raise SemesterNotFoundException()

        section_data = section.model_dump()
        db_section = Section(**section_data)

        try:
            self.db.add(db_section)
            self.db.commit()
            self.db.refresh(db_section)
            return db_section
        except IntegrityError as e:
            self.db.rollback()
            logger.error("Integrity error while creating section for user %s: %s",
                         user_id, e, exc_info=True)
            raise AppException() from e

    def update_section(self, section_id: int,
                       user_id: str, updated_section: SectionUpdate):
        """Update an existing section in the database."""
        db_section = self.get_section(section_id, user_id)
        update_data = updated_section.model_dump()

        for key, value in update_data.items():
            setattr(db_section, key, value)

        try:
            self.db.commit()
            self.db.refresh(db_section)
            logger.info("Section with id %s updated for user %s.",
                        section_id, user_id)
            return db_section
        except IntegrityError as e:
            self.db.rollback()
            logger.error("Integrity error while updating section %s for user %s: %s",
                         section_id, user_id, e, exc_info=True)
            raise AppException() from e

    def delete_section(self, section_id: int, user_id: str):
        """Soft delete a section from the database."""
        db_section = self.get_section(section_id, user_id)

        try:
            # Soft delete associated statistics
            self.db.query(Statistics).filter(
                Statistics.id_section == section_id,
                Statistics.is_deleted.is_(False)
            ).update(
                {
                    Statistics.is_deleted: True,
                    Statistics.deleted_at: func.now()
                },
                synchronize_session=False
            )

            # Soft delete the section
            db_section.is_deleted = True
            db_section.deleted_at = func.now()

            self.db.commit()
            self.db.refresh(db_section)
            logger.info("Section with id %s soft deleted for user %s.",
                        section_id, user_id)
            return db_section
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error("Error occurred while soft deleting section %s for user %s: %s",
                         section_id, user_id, e, exc_info=True)
            raise AppException() from e
