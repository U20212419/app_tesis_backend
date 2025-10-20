"""Model definition for Statistics table."""

from sqlalchemy import JSON, Column, ForeignKey, Integer
from sqlalchemy.orm import relationship

from app.db import Base

class Statistics(Base):
    """Statistics model."""
    __tablename__ = "Statistics"

    id_section = Column(Integer, ForeignKey("Section.id_section"), primary_key=True)
    id_assessment = Column(Integer, ForeignKey("Assessment.id_assessment"), primary_key=True)
    stats = Column(JSON, nullable=False)

    section = relationship(
        "Section", back_populates="statistics"
    )
    assessment = relationship(
        "Assessment", back_populates="statistics"
    )
