"""Schemas for Course operations."""

from pydantic import BaseModel

class CourseBase(BaseModel):
    """Base schema for Course."""
    name: str
    code: str

class CourseCreate(CourseBase):
    """Schema for creating a Course."""

class CourseRead(CourseBase):
    """Schema for reading a Course."""
    id_course: int
    class Config:
        """Enable ORM mode for compatibility with SQLAlchemy models."""
        orm_mode = True
