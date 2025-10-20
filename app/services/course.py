"""Service for handling course-related operations."""

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.course_in_semester import CourseInSemester
from app.schemas.course import CourseCreate

def get_all_courses(db: Session, user_id: str):
    """Retrieve all courses for a specific user."""
    return db.query(Course).filter(Course.id_user == user_id).all()

def get_course(db: Session, course_id: int, user_id: str):
    """Retrieve a specific course by its ID, only if it belongs to the user."""
    return db.query(Course).filter(
            Course.id_course == course_id,
            Course.id_user == user_id
        ).first()

def create_course(db: Session, course: CourseCreate, user_id: str):
    """Create a new course in the database."""
    db_course = Course(**course.model_dump(), id_user=user_id)
    db.add(db_course)
    db.commit()
    db.refresh(db_course)
    return db_course

def get_all_courses_detailed(db: Session, user_id: str):
    """Retrieve all courses for a specific user,
    including the amount of semesters in which each course is present.
    """
    results = (
        db.query(
            Course,
            # pylint: disable=not-callable
            func.count(CourseInSemester.Semester_id_semester).label("semester_count")
        )
        .outerjoin(CourseInSemester, Course.id_course == CourseInSemester.Course_id_course)
        .filter(Course.id_user == user_id)
        .group_by(Course.id_course)
        .all()
    )

    return [
        (setattr(course, "semester_count", semester_count or 0) or course)
        for course, semester_count in results
    ]
