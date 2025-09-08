"""Schemas for Section operations."""

from pydantic import BaseModel

class SectionBase(BaseModel):
    """Base schema for Section."""
    name: str
    id_semester: int
    id_course: int

class SectionCreate(SectionBase):
    """Schema for creating a Section."""

class SectionRead(SectionBase):
    """Schema for reading a Section."""
    id_section: int
    class Config:
        """Enable ORM mode for compatibility with SQLAlchemy models."""
        orm_mode = True
