"""Model definition for Assessment table."""

from sqlalchemy import Column, Integer, String
from ..db import Base

class Assessment(Base):
    """Assessment model."""
    __tablename__ = "Assessment"
    id_assessment = Column(Integer, primary_key=True, index=True)
    type = Column(String(45), nullable=False)
    number = Column(Integer, nullable=False)
    question_amount = Column(Integer, nullable=True)
    id_semester = Column(Integer, nullable=False)
    id_course = Column(Integer, nullable=False)
