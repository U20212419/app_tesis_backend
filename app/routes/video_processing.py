from fastapi import APIRouter, BackgroundTasks, Depends, status

from app.auth.auth_utils import get_current_user_id
from app.schemas.statistics import StatisticsUpdate
from app.schemas.video import (
    GenerateUploadUrlRequest,
    GenerateUploadUrlResponse,
    VideoProcessRequest
)
from app.services.statistics import StatisticsService

router = APIRouter(prefix="/video-processing", tags=["video-processing"])

@router.post("/", status_code=status.HTTP_202_ACCEPTED)
def trigger_video_processing(request: VideoProcessRequest,
                             background_tasks: BackgroundTasks,
                             stats_service: StatisticsService = Depends(),
                             user_id: str = Depends(get_current_user_id)):
    """Trigger background video processing task.

    Args:
        request (VideoProcessRequest): Video processing request data.
        background_tasks (BackgroundTasks): FastAPI background tasks manager.
        stats_service (StatisticsService): Service for statistics operations.
        user_id (str): ID of the current user.
    
    Returns:
        dict: Confirmation message.
    """
    # Validate assessment and section ownership
    stats_service._get_validated_assessment_and_section(
        user_id,
        request.id_assessment,
        request.id_section
    )

    # Invalidate any existing statistics for this assessment and section
    stats_service.create_or_update_statistics(
        request.id_assessment,
        request.id_section,
        stats_data=None,
        user_id=user_id,
        status="STALE"
    )

    # Schedule the video processing task in the background
    background_tasks.add_task(
        stats_service.process_and_save_video,
        s3_url=request.s3_url,
        question_amount=request.question_amount,
        assessment_id=request.id_assessment,
        section_id=request.id_section,
        user_id=user_id,
        frames_indexes=request.frames_indexes
    )

    return {"message": "Video processing has been started."}

@router.post("/generate-upload-url", status_code=status.HTTP_200_OK)
def generate_video_upload_url(request: GenerateUploadUrlRequest,
                              stats_service: StatisticsService = Depends(),
                              user_id: str = Depends(get_current_user_id)):
    """Generate a pre-signed S3 URL for video upload.

    Args:
        request (GenerateUploadUrlRequest): Request data for generating upload URL.
        stats_service (StatisticsService): Service for statistics operations.
        user_id (str): ID of the current user.
    
    Returns:
        GenerateUploadUrlResponse: Response containing the pre-signed URL and related data.
    """
    url_data = stats_service.get_presigned_upload_url(
        file_name=request.file_name,
        user_id=user_id
    )
    return GenerateUploadUrlResponse(**url_data)
