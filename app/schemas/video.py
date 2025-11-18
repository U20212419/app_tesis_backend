"""Schemas for video processing."""

from typing import List, Optional
from pydantic import BaseModel

class GenerateUploadUrlRequest(BaseModel):
    """Schema for generating video upload URL request."""
    file_name: str

class GenerateUploadUrlResponse(BaseModel):
    """Schema for generating video upload URL response."""
    upload_url: str
    download_url: str

class VideoProcessRequest(BaseModel):
    """Schema for video processing request."""
    s3_url: str
    id_assessment: int
    id_section: int
    question_amount: int
    frames_indexes: Optional[List[int]] = None
