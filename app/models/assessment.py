"""Model definition for Assessment table."""

from sqlalchemy import Column, ForeignKeyConstraint, Integer, String
from sqlalchemy.orm import relationship

from app.db import Base

class Assessment(Base):
    """Assessment model."""
    __tablename__ = "Assessment"

    id_assessment = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(String(45), nullable=False)
    number = Column(Integer, nullable=False)
    question_amount = Column(Integer, nullable=True)

    id_semester = Column(Integer, nullable=False)
    id_course = Column(Integer, nullable=False)

    __table_args__ = (
        ForeignKeyConstraint(
            ["id_semester", "id_course"],
            ["CourseInSemester.Semester_id_semester", "CourseInSemester.Course_id_course"]
        ),
    )

    course_in_semester = relationship(
        "CourseInSemester", back_populates="assessments", foreign_keys=[id_semester, id_course]
    )
    statistics = relationship(
        "Statistics", back_populates="assessment", cascade="all, delete-orphan"
    )
