"""Model definition for Statistics table."""

from datetime import datetime
from typing import Any, Dict, Optional
from sqlalchemy import Boolean, JSON, ForeignKey, Integer, TIMESTAMP, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db import Base

class Statistics(Base):
    """Statistics model."""
    __tablename__ = "Statistics"

    id_section: Mapped[int] = mapped_column(
        Integer, ForeignKey("Section.id_section"), primary_key=True
    )
    id_assessment: Mapped[int] = mapped_column(
        Integer, ForeignKey("Assessment.id_assessment"), primary_key=True
    )
    stats: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)

    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True),
                                                 server_default=func.now(),
                                                 nullable=False)
    modified_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True),
                                                  server_default=func.now(),
                                                  onupdate=func.now(),
                                                  nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)

    status: Mapped[str] = mapped_column(String(30), nullable=False)

    section: Mapped["Section"] = relationship( # type: ignore
        "Section", back_populates="statistics"
    )
    assessment: Mapped["Assessment"] = relationship( # type: ignore
        "Assessment", back_populates="statistics"
    )
