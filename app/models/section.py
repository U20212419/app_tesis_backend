"""Model definition for Section table."""

from sqlalchemy import Column, ForeignKeyConstraint, Integer, String
from sqlalchemy.orm import relationship

from app.db import Base

class Section(Base):
    """Section model."""
    __tablename__ = "Section"

    id_section = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(45), nullable=False)

    id_semester = Column(Integer, nullable=False)
    id_course = Column(Integer, nullable=False)

    __table_args__ = (
        ForeignKeyConstraint(
            ["id_semester", "id_course"],
            ["CourseInSemester.Semester_id_semester", "CourseInSemester.Course_id_course"]
        ),
    )

    course_in_semester = relationship(
        "CourseInSemester", back_populates="sections", foreign_keys=[id_semester, id_course]
    )
    statistics = relationship(
        "Statistics", back_populates="section", cascade="all, delete-orphan"
    )
