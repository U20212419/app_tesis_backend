"""Model definition for Section table."""

from datetime import datetime
from typing import Optional
from sqlalchemy import Boolean, ForeignKeyConstraint, Integer, String, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db import Base

class Section(Base):
    """Section model."""
    __tablename__ = "Section"

    id_section: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(20), nullable=False)

    id_semester: Mapped[int] = mapped_column(Integer, nullable=False)
    id_course: Mapped[int] = mapped_column(Integer, nullable=False)

    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True),
                                                 server_default=func.now(),
                                                 nullable=False)
    modified_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True),
                                                  server_default=func.now(),
                                                  onupdate=func.now(),
                                                  nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)

    __table_args__ = (
        ForeignKeyConstraint(
            ["id_semester", "id_course"],
            ["CourseInSemester.Semester_id_semester", "CourseInSemester.Course_id_course"]
        ),
    )

    course_in_semester: Mapped["CourseInSemester"] = relationship( # type: ignore
        "CourseInSemester", back_populates="sections", foreign_keys=[id_semester, id_course]
    )
    statistics: Mapped["Statistics"] = relationship( # type: ignore
        "Statistics", back_populates="section", cascade="all, delete-orphan"
    )
