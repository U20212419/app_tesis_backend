"""Model definition for CourseInSemester table."""

from sqlalchemy import Column, ForeignKey, Integer
from ..db import Base

class CourseInSemester(Base):
    """CourseInSemester model."""
    __tablename__ = "CourseInSemester"
    Semester_id_semester = Column(Integer, ForeignKey("Semester.id_semester"), primary_key=True)
    Course_id_course = Column(Integer, ForeignKey("Course.id_course"), primary_key=True)
