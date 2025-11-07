"""Service for handling course-related operations."""

from fastapi import Depends
from sqlalchemy import and_
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from app.db import get_db
from app.models.course import Course
from app.models.course_in_semester import CourseInSemester
from app.schemas.course import CourseCreate

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
        return self.db.query(Course).filter(
                Course.id_course == course_id,
                Course.id_user == user_id,
                Course.is_deleted.is_(False)
            ).first()

    def create_course(self, course: CourseCreate, user_id: str):
        """Create a new course in the database."""
        course_data = course.model_dump()
        db_course = Course(
            **course_data,
            id_user=user_id,
            active_code=course_data['code']
        )
        self.db.add(db_course)
        self.db.commit()
        self.db.refresh(db_course)
        db_course.semester_count = 0
        return db_course

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
        if db_course:
            update_data = updated_course.model_dump()
            for key, value in update_data.items():
                setattr(db_course, key, value)
            if 'code' in update_data:
                db_course.active_code = update_data['code']
            self.db.commit()
            self.db.refresh(db_course)
        return db_course

    def delete_course(self, course_id: int, user_id: str):
        """Soft delete a course from the database."""
        db_course = self.get_course(course_id, user_id)
        if db_course:
            db_course.is_deleted = True
            db_course.deleted_at = func.now()
            db_course.active_code = None
            self.db.commit()
            self.db.refresh(db_course)
        return db_course
