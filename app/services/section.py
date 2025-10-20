"""Service for handling section-related operations."""

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.course_in_semester import CourseInSemester
from app.models.semester import Semester
from app.models.section import Section
from app.schemas.section import SectionCreate

def get_all_sections(db: Session, user_id: str):
    """Retrieve all sections for a specific user."""
    return (
        db.query(Section)
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
            Semester.id_user == user_id
        )
        .all()
    )

def get_section(db: Session, section_id: int, user_id: str):
    """Retrieve a specific section by its ID, only if it belongs to the user."""
    return (
        db.query(Section)
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
            Semester.id_user == user_id
        )
        .first()
    )

def create_section(db: Session, section: SectionCreate, user_id: str):
    """Create a new section in the database,
    only if the course and semester belong to the user.
    """
    course = db.query(Course).filter(
        Course.id_course == section.id_course,
        Course.id_user == user_id
    ).first()
    if not course:
        raise ValueError("Course does not belong to the user.")

    semester = db.query(Semester).filter(
        Semester.id_semester == section.id_semester,
        Semester.id_user == user_id
    ).first()
    if not semester:
        raise ValueError("Semester does not belong to the user.")

    db_section = Section(**section.model_dump())
    db.add(db_section)
    db.commit()
    db.refresh(db_section)
    return db_section
