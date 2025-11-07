"""Schemas for Course operations."""

from typing import Optional
from pydantic import BaseModel, ConfigDict

class CourseBase(BaseModel):
    """Base schema for Course."""
    name: str
    code: str

class CourseCreate(CourseBase):
    """Schema for creating a Course."""

class CourseRead(CourseBase):
    """Schema for reading a Course."""
    id_course: int
    semester_count: Optional[int] = None
    model_config = ConfigDict(from_attributes=True)
