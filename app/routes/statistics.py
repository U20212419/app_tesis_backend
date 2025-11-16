"""Routes for managing statistics."""
from fastapi import APIRouter, Depends, Response, status

from app.auth.auth_utils import get_current_user_id
from app.schemas.statistics import StatisticsRead, StatisticsUpdate
from app.services.statistics import StatisticsService

router = APIRouter(prefix="/statistics", tags=["statistics"])

@router.get("/{assessment_id}/{section_id}", response_model=StatisticsRead)
def read_statistics(assessment_id: int, section_id: int,
                   statistics_service: StatisticsService = Depends(),
                   user_id: str = Depends(get_current_user_id)):
    """Get statistics for a specific assessment and section.
    
    Args:
        assessment_id (int): ID of the assessment.
        section_id (int): ID of the section.
        statistics_service (StatisticsService): Service for statistics operations.
        user_id (str): ID of the current user.
    
    Returns:
        StatisticsRead: The statistics for the specified assessment and section.
    """
    return statistics_service.get_statistics(assessment_id, section_id, user_id)

@router.put("/{assessment_id}/{section_id}", response_model=StatisticsRead)
def update_statistics(assessment_id: int, section_id: int,
                      updated_statistics: StatisticsUpdate,
                      statistics_service: StatisticsService = Depends(),
                      user_id: str = Depends(get_current_user_id)):
    """Recalculate and update statistics for a specific assessment and section.

    Args:
        assessment_id (int): ID of the assessment.
        section_id (int): ID of the section.
        statistics_service (StatisticsService): Service for statistics operations.
        user_id (str): ID of the current user.
    
    Returns:
        Response: HTTP 204 No Content response.
    """
    return statistics_service.update_statistics(
        assessment_id,
        section_id,
        updated_statistics,
        user_id
    )

@router.delete("/{assessment_id}/{section_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_statistics(assessment_id: int, section_id: int,
                      statistics_service: StatisticsService = Depends(),
                      user_id: str = Depends(get_current_user_id)):
    """Soft delete statistics for a specific assessment and section.
    
    Args:
        assessment_id (int): ID of the assessment.
        section_id (int): ID of the section.
        statistics_service (StatisticsService): Service for statistics operations.
        user_id (str): ID of the current user.

    Returns:
        Response: HTTP 204 No Content response.
    """
    statistics_service.delete_statistics(assessment_id, section_id, user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
