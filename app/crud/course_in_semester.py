"""CRUD operations for the CourseInSemester model."""

from sqlalchemy.orm import Session
from ..models.course_in_semester import CourseInSemester
from ..schemas.course_in_semester import CourseInSemesterCreate

def get_all_courses_in_semester(db: Session):
    """Retrieve all courses in a semester from the database."""
    return db.query(CourseInSemester).all()

def get_course_in_semester(db: Session, semester_id: int, course_id):
    """Retrieve a specific course in a semester by their IDs."""
    return db.query(CourseInSemester).filter(
        CourseInSemester.id_semester == semester_id,
        CourseInSemester.id_course == course_id
    ).first()

def create_course_in_semester(db: Session, course_in_semester: CourseInSemesterCreate):
    """Create a new course in semester in the database."""
    db_course_in_semester = CourseInSemester(**course_in_semester.model_dump())
    db.add(db_course_in_semester)
    db.commit()
    db.refresh(db_course_in_semester)
    return db_course_in_semester
