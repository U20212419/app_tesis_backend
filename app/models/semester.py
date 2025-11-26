"""Model definition for Semester table."""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import Boolean, Integer, String, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db import Base

class Semester(Base):
    """Semester model."""
    __tablename__ = "Semester"

    id_semester: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    number: Mapped[int] = mapped_column(Integer, nullable=False)
    id_user: Mapped[str] = mapped_column(String(100), nullable=False)

    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True),
                                                 server_default=func.now(),
                                                 nullable=False)
    modified_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True),
                                                  server_default=func.now(),
                                                  onupdate=func.now(),
                                                  nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)

    active_semester_key: Mapped[Optional[str]] = mapped_column(
        String(110), nullable=True, unique=True
    )

    courses_in_semester: Mapped[List["CourseInSemester"]] = relationship( # type: ignore
        "CourseInSemester", back_populates="semester"
    )
