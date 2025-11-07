"""Schemas for Semester operations."""

from typing import Optional
from pydantic import BaseModel, ConfigDict

class SemesterBase(BaseModel):
    """Base schema for Semester."""
    year: int
    number: int

class SemesterCreate(SemesterBase):
    """Schema for creating a Semester."""

class SemesterRead(SemesterBase):
    """Schema for reading a Semester."""
    id_semester: int
    course_count: Optional[int] = None
    model_config = ConfigDict(from_attributes=True)
