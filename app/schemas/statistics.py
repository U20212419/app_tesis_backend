"""Schemas for Statistics operations."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict

class StatisticsBase(BaseModel):
    """Base schema for Statistics."""
    stats: Dict[str, Any]
    id_assessment: int
    id_section: int
    status: str

class StatisticsCreate(StatisticsBase):
    """Schema for creating a Statistics."""

class StatisticsUpdate(BaseModel):
    scores: Optional[List[Dict[str, Any]]] = None
    status: Optional[str] = None

class StatisticsRead(StatisticsBase):
    """Schema for reading a Statistics."""
    model_config = ConfigDict(from_attributes=True)
