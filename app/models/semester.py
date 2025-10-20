"""Model definition for Semester table."""

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.db import Base

class Semester(Base):
    """Semester model."""
    __tablename__ = "Semester"

    id_semester = Column(Integer, primary_key=True, autoincrement=True)
    year = Column(Integer, nullable=False)
    number = Column(Integer, nullable=False)
    id_user = Column(String(100), nullable=False)

    courses_in_semester = relationship(
        "CourseInSemester", back_populates="semester"
    )
