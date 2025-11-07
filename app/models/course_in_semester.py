"""Model definition for CourseInSemester table."""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import Boolean, ForeignKey, Integer, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db import Base

class CourseInSemester(Base):
    """CourseInSemester model."""
    __tablename__ = "CourseInSemester"

    Semester_id_semester: Mapped[int] = mapped_column(
        Integer, ForeignKey("Semester.id_semester"), primary_key=True
    )
    Course_id_course: Mapped[int] = mapped_column(
        Integer, ForeignKey("Course.id_course"), primary_key=True
    )

    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True),
                                                 server_default=func.now(),
                                                 nullable=False)
    modified_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True),
                                                  server_default=func.now(),
                                                  onupdate=func.now(),
                                                  nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)

    semester: Mapped["Semester"] = relationship( # type: ignore
        "Semester", back_populates="courses_in_semester"
    )
    course: Mapped["Course"] = relationship( # type: ignore
        "Course", back_populates="courses_in_semester"
    )

    assessments: Mapped[List["Assessment"]] = relationship( # type: ignore
        "Assessment", back_populates="course_in_semester", cascade="all, delete-orphan",
        foreign_keys="[Assessment.id_semester, Assessment.id_course]"
    )
    sections: Mapped[List["Section"]] = relationship( # type: ignore
        "Section", back_populates="course_in_semester", cascade="all, delete-orphan",
        foreign_keys="[Section.id_semester, Section.id_course]"
    )
