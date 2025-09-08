"""Model definition for Section table."""

from sqlalchemy import Column, Integer, String
from ..db import Base

class Section(Base):
    """Section model."""
    __tablename__ = "Section"
    id_section = Column(Integer, primary_key=True, index=True)
    name = Column(String(45), nullable=False)
    id_semester = Column(Integer, nullable=False)
    id_course = Column(Integer, nullable=False)
