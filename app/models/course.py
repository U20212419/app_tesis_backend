"""Model definition for Course table."""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import Boolean, Integer, String, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db import Base

class Course(Base):
    """Course model."""
    __tablename__ = "Course"

    id_course: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(10), nullable=False)
    id_user: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True),
                                                 server_default=func.now(),
                                                 nullable=False)
    modified_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True),
                                                  server_default=func.now(),
                                                  onupdate=func.now(),
                                                  nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)

    active_code: Mapped[Optional[str]] = mapped_column(String(10), nullable=True, unique=True)

    courses_in_semester: Mapped[List["CourseInSemester"]] = relationship( # type: ignore
        "CourseInSemester", back_populates="course"
    )
