"""CRUD operations for the Course model."""

from sqlalchemy.orm import Session
from ..models.course import Course
from ..schemas.course import CourseCreate

def get_all_courses(db: Session):
    """Retrieve all courses from the database."""
    return db.query(Course).all()

def get_course(db: Session, course_id: int):
    """Retrieve a specific course by its ID."""
    return db.query(Course).filter(Course.id_course == course_id).first()

def create_course(db: Session, course: CourseCreate):
    """Create a new course in the database."""
    db_course = Course(**course.model_dump())
    db.add(db_course)
    db.commit()
    db.refresh(db_course)
    return db_course
