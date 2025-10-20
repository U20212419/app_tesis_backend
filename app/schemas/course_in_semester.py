"""Schemas for CourseInSemester operations."""

from typing import Optional
from pydantic import BaseModel

from app.schemas.course import CourseRead

class CourseInSemesterBase(BaseModel):
    """Base schema for CourseInSemester."""
    semester_id: int
    course_id: int

class CourseInSemesterCreate(CourseInSemesterBase):
    """Schema for creating a CourseInSemester."""

class CourseInSemesterRead(CourseInSemesterBase):
    """Schema for reading a CourseInSemester."""
    assessment_count: Optional[int] = None
    section_count: Optional[int] = None
    course: Optional[CourseRead] = None
    class Config:
        """Enable ORM mode for compatibility with SQLAlchemy models."""
        orm_mode = True
