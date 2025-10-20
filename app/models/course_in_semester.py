"""Model definition for CourseInSemester table."""

from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.orm import relationship

from app.db import Base

class CourseInSemester(Base):
    """CourseInSemester model."""
    __tablename__ = "CourseInSemester"

    Semester_id_semester = Column(Integer, ForeignKey("Semester.id_semester"), primary_key=True)
    Course_id_course = Column(Integer, ForeignKey("Course.id_course"), primary_key=True)

    semester = relationship(
        "Semester", back_populates="courses_in_semester"
    )
    course = relationship(
        "Course", back_populates="courses_in_semester"
    )

    assessments = relationship(
        "Assessment", back_populates="course_in_semester", cascade="all, delete-orphan",
        foreign_keys="[Assessment.id_semester, Assessment.id_course]"
    )
    sections = relationship(
        "Section", back_populates="course_in_semester", cascade="all, delete-orphan",
        foreign_keys="[Section.id_semester, Section.id_course]"
    )
