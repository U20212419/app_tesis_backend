"""Service for handling semester-related operations."""

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.course_in_semester import CourseInSemester
from app.models.semester import Semester
from app.schemas.semester import SemesterCreate

def get_all_semesters(db: Session, user_id: str):
    """Retrieve all semesters for a specific user."""
    return db.query(Semester).filter(Semester.id_user == user_id).all()

def get_semester(db: Session, semester_id: int, user_id: str):
    """Retrieve a specific semester by its ID, only if it belongs to the user."""
    return db.query(Semester).filter(
            Semester.id_semester == semester_id,
            Semester.id_user == user_id
        ).first()

def create_semester(db: Session, semester: SemesterCreate, user_id: str):
    """Create a new semester in the database."""
    db_semester = Semester(**semester.model_dump(), id_user=user_id)
    db.add(db_semester)
    db.commit()
    db.refresh(db_semester)
    return db_semester

def get_all_semesters_detailed(db: Session, user_id: str):
    """Retrieve all semesters for a specific user,
    including the amount of courses that are present in each semester.
    """
    results = (
        db.query(
            Semester,
            # pylint: disable=not-callable
            func.count(CourseInSemester.Course_id_course).label("course_count")
        )
        .outerjoin(CourseInSemester, Semester.id_semester == CourseInSemester.Semester_id_semester)
        .filter(Semester.id_user == user_id)
        .group_by(Semester.id_semester)
        .all()
    )

    return [
        (setattr(semester, "course_count", course_count or 0) or semester)
        for semester, course_count in results
    ]
