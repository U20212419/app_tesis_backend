"""Schemas for Section operations."""

from pydantic import BaseModel, ConfigDict

class SectionBase(BaseModel):
    """Base schema for Section."""
    name: str
    id_semester: int
    id_course: int

class SectionCreate(SectionBase):
    """Schema for creating a Section."""

class SectionUpdate(BaseModel):
    """Schema for updating a Section."""
    name: str

class SectionRead(SectionBase):
    """Schema for reading a Section."""
    id_section: int
    model_config = ConfigDict(from_attributes=True)
