"""Schemas for Semester operations."""

from pydantic import BaseModel

class SemesterBase(BaseModel):
    """Base schema for Semester."""
    year: int
    number: int

class SemesterCreate(SemesterBase):
    """Schema for creating a Semester."""

class SemesterRead(SemesterBase):
    """Schema for reading a Semester."""
    id_semester: int
    class Config:
        """Enable ORM mode for compatibility with SQLAlchemy models."""
        orm_mode = True
