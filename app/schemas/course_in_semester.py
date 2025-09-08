"""Schemas for CourseInSemester operations."""

from pydantic import BaseModel

class CourseInSemesterBase(BaseModel):
    """Base schema for CourseInSemester."""
    semester_id: int
    course_id: int

class CourseInSemesterCreate(CourseInSemesterBase):
    """Schema for creating a CourseInSemester."""

class CourseInSemesterRead(CourseInSemesterBase):
    """Schema for reading a CourseInSemester."""
    class Config:
        """Enable ORM mode for compatibility with SQLAlchemy models."""
        orm_mode = True
