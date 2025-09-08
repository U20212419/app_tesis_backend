"""Schemas for Assessment operations."""

from pydantic import BaseModel

class AssessmentBase(BaseModel):
    """Base schema for Assessment."""
    type: str
    number: int
    question_amount: int | None = None
    id_semester: int
    id_course: int

class AssessmentCreate(AssessmentBase):
    """Schema for creating a Assessment."""

class AssessmentRead(AssessmentBase):
    """Schema for reading a Assessment."""
    id_assessment: int
    class Config:
        """Enable ORM mode for compatibility with SQLAlchemy models."""
        orm_mode = True
