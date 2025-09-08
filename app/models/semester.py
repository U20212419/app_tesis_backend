"""Model definition for Semester table."""

from sqlalchemy import Column, Integer, UniqueConstraint
from ..db import Base

class Semester(Base):
    """Semester model."""
    __tablename__ = "Semester"
    id_semester = Column(Integer, primary_key=True, index=True)
    year = Column(Integer, nullable=False)
    number = Column(Integer, nullable=False)

    __table_args__ = (UniqueConstraint("year", "number", name="unique_semester"),)
