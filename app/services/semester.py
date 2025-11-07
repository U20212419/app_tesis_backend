"""Service for handling semester-related operations."""

from fastapi import Depends
from sqlalchemy import and_
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from app.db import get_db
from app.models.course_in_semester import CourseInSemester
from app.models.semester import Semester
from app.schemas.semester import SemesterCreate

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
        return self.db.query(Semester).filter(
                Semester.id_semester == semester_id,
                Semester.id_user == user_id,
                Semester.is_deleted.is_(False)
            ).first()

    def create_semester(self, semester: SemesterCreate, user_id: str):
        """Create a new semester in the database."""
        semester_data = semester.model_dump()
        semester_key = f"{semester_data['year']}-{semester_data['number']}"
        db_semester = Semester(
            **semester_data,
            id_user=user_id,
            active_semester_key=semester_key
        )
        self.db.add(db_semester)
        self.db.commit()
        self.db.refresh(db_semester)
        db_semester.courses_count = 0
        return db_semester

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
        if db_semester:
            update_data = updated_semester.model_dump()
            for key, value in updated_semester.model_dump().items():
                setattr(db_semester, key, value)
            if 'year' in update_data or 'number' in update_data:
                semester_key = f"{db_semester.year}-{db_semester.number}"
                db_semester.active_semester_key = semester_key
            self.db.commit()
            self.db.refresh(db_semester)
        return db_semester
    
    def delete_semester(self, semester_id: int, user_id: str):
        """Soft delete a semester from the database."""
        db_semester = self.get_semester(semester_id, user_id)
        if db_semester:
            db_semester.is_deleted = True
            db_semester.deleted_at = func.now()
            db_semester.active_semester_key = None
            self.db.commit()
            self.db.refresh(db_semester)
        return db_semester
