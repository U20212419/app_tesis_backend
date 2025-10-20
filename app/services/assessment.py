"""Service for handling assessment-related operations."""

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.course_in_semester import CourseInSemester
from app.models.semester import Semester
from app.models.assessment import Assessment
from app.schemas.assessment import AssessmentCreate

def get_all_assessments(db: Session, user_id: str):
    """Retrieve all assessments for a specific course in semester,
    only if it belongs to the user.
    """
    return (
        db.query(Assessment)
        .join(CourseInSemester,
              and_(
                  Assessment.id_course == CourseInSemester.Course_id_course,
                  Assessment.id_semester == CourseInSemester.Semester_id_semester
              )
        )
        .join(Course, CourseInSemester.Course_id_course == Course.id_course)
        .join(Semester, CourseInSemester.Semester_id_semester == Semester.id_semester)
        .filter(
            Course.id_user == user_id,
            Semester.id_user == user_id
        )
        .all()
    )

def get_assessment(db: Session, assessment_id: int, user_id: str):
    """Retrieve a specific assessment by its ID, only if it belongs to the user."""
    return (
        db.query(Assessment)
        .join(CourseInSemester,
              and_(
                  Assessment.id_course == CourseInSemester.Course_id_course,
                  Assessment.id_semester == CourseInSemester.Semester_id_semester
              )
        )
        .join(Course, CourseInSemester.Course_id_course == Course.id_course)
        .join(Semester, CourseInSemester.Semester_id_semester == Semester.id_semester)
        .filter(
            Assessment.id_assessment == assessment_id,
            Course.id_user == user_id,
            Semester.id_user == user_id
        )
        .first()
    )

def create_assessment(db: Session, assessment: AssessmentCreate, user_id: str):
    """Create a new assessment in the database,
    only if the course and semester belong to the user.
    """
    course = db.query(Course).filter(
        Course.id_course == assessment.id_course,
        Course.id_user == user_id
    ).first()
    if not course:
        raise ValueError("Course does not belong to the user.")

    semester = db.query(Semester).filter(
        Semester.id_semester == assessment.id_semester,
        Semester.id_user == user_id
    ).first()
    if not semester:
        raise ValueError("Semester does not belong to the user.")

    db_assessment = Assessment(**assessment.model_dump())
    db.add(db_assessment)
    db.commit()
    db.refresh(db_assessment)
    return db_assessment
