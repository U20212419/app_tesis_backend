"""Model definition for Course table."""

from sqlalchemy import Column, Integer, String
from ..db import Base

class Course(Base):
    """Course model."""
    __tablename__ = "Course"
    id_course = Column(Integer, primary_key=True, index=True)
    name = Column(String(45), nullable=False)
    code = Column(String(45), nullable=False, unique=True)
