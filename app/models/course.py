"""Model definition for Course table."""

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.db import Base

class Course(Base):
    """Course model."""
    __tablename__ = "Course"

    id_course = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(45), nullable=False)
    code = Column(String(45), nullable=False, unique=True)
    id_user = Column(String(100), nullable=False)

    courses_in_semester = relationship(
        "CourseInSemester", back_populates="course"
    )
