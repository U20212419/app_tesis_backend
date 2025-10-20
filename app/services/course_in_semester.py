"""Service for handling course-in-semester-related operations."""

from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.semester import Semester
from app.models.course_in_semester import CourseInSemester
from app.schemas.course_in_semester import CourseInSemesterCreate

def get_all_courses_in_semester(db: Session, user_id: str):
    """Retrieve all courses in a semester, only if they belong to the user."""
    return (
        db.query(CourseInSemester)
        .join(Course, CourseInSemester.Course_id_course == Course.id_course)
        .join(Semester, CourseInSemester.Semester_id_semester == Semester.id_semester)
        .filter(
            Course.id_user == user_id,
            Semester.id_user == user_id
        )
        .all()
    )

def get_course_in_semester(db: Session, semester_id: int, course_id, user_id: str):
    """Retrieve a specific course in a semester by their IDs, only if they belong to the user."""
    return (
        db.query(CourseInSemester)
        .join(Course, CourseInSemester.Course_id_course == Course.id_course)
        .join(Semester, CourseInSemester.Semester_id_semester == Semester.id_semester)
        .filter(
            CourseInSemester.id_course == course_id,
            CourseInSemester.id_semester == semester_id,
            Course.id_user == user_id,
            Semester.id_user == user_id
        )
        .first()
    )

def create_course_in_semester(db: Session, course_in_semester: CourseInSemesterCreate,
                              user_id: str):
    """Create a new course in semester in the database, only if they belong to the user."""
    course = db.query(Course).filter(
        Course.id_course == course_in_semester.course_id,
        Course.id_user == user_id
    ).first()
    if not course:
        raise ValueError("Course does not belong to the user.")

    semester = db.query(Semester).filter(
        Semester.id_semester == course_in_semester.semester_id,
        Semester.id_user == user_id
    ).first()
    if not semester:
        raise ValueError("Semester does not belong to the user.")

    db_course_in_semester = CourseInSemester(**course_in_semester.model_dump())
    db.add(db_course_in_semester)
    db.commit()
    db.refresh(db_course_in_semester)
    return db_course_in_semester
