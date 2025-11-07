"""Schemas for CourseInSemester operations."""

from typing import Optional
from pydantic import BaseModel, ConfigDict

from app.schemas.course import CourseRead

class CourseInSemesterBase(BaseModel):
    """Base schema for CourseInSemester."""
    Semester_id_semester: int
    Course_id_course: int

class CourseInSemesterCreate(CourseInSemesterBase):
    """Schema for creating a CourseInSemester."""

class CourseInSemesterRead(CourseInSemesterBase):
    """Schema for reading a CourseInSemester."""
    assessment_count: Optional[int] = None
    section_count: Optional[int] = None
    course: Optional[CourseRead] = None
    model_config = ConfigDict(from_attributes=True)
