"""Routes for managing assessments."""

from fastapi import APIRouter, Depends, Response, status

from app.auth.auth_utils import get_current_user_id
from app.schemas.assessment import AssessmentCreate, AssessmentRead, AssessmentUpdate
from app.services.assessment import AssessmentService

router = APIRouter(prefix="/assessments", tags=["assessments"])

@router.get("/{semester_id}/{course_id}", response_model=list[AssessmentRead])
def read_assessments(semester_id: int, course_id: int,
                     assessment_service: AssessmentService = Depends(),
                     user_id: str = Depends(get_current_user_id)):
    """Get all assessments for a specific course in a semester.
    
    Args:
        semester_id (int): ID of the semester.
        course_id (int): ID of the course.
        assessment_service (AssessmentService): Service for assessment operations.
        user_id (str): ID of the current user.

    Returns:
        list[AssessmentRead]: List of assessments for the specified course and semester.
    """
    return assessment_service.get_all_assessments(semester_id, course_id, user_id)

@router.post("/", response_model=AssessmentRead)
def add_assessment(assessment: AssessmentCreate,
                   assessment_service: AssessmentService = Depends(),
                   user_id: str = Depends(get_current_user_id)):
    """Create a new assessment.
    
    Args:
        assessment (AssessmentCreate): Assessment data.
        assessment_service (AssessmentService): Service for assessment operations.
        user_id (str): ID of the current user.
        
    Returns:
        AssessmentRead: The created assessment.
    """
    return assessment_service.create_assessment(assessment, user_id)

@router.get("/{assessment_id}", response_model=AssessmentRead)
def read_assessment(assessment_id: int, assessment_service: AssessmentService = Depends(),
                    user_id: str = Depends(get_current_user_id)):
    """Get an assessment by ID.
    
    Args:
        assessment_id (int): ID of the assessment.
        assessment_service (AssessmentService): Service for assessment operations.
        user_id (str): ID of the current user.
        
    Returns:
        AssessmentRead: The requested assessment.
    """
    return assessment_service.get_assessment(assessment_id, user_id)

@router.put("/{assessment_id}", response_model=AssessmentRead)
def update_assessment(assessment_id: int, updated_assessment: AssessmentUpdate,
                      assessment_service: AssessmentService = Depends(),
                      user_id: str = Depends(get_current_user_id)):
    """Update an assessment by ID.
    
    Args:
        assessment_id (int): ID of the assessment.
        updated_assessment (AssessmentCreate): Updated assessment data.
        assessment_service (AssessmentService): Service for assessment operations.
        user_id (str): ID of the current user.
        
    Returns:
        AssessmentRead: The updated assessment.
    """
    return assessment_service.update_assessment(assessment_id, user_id, updated_assessment)

@router.delete("/{assessment_id}", response_model=AssessmentRead)
def delete_assessment(assessment_id: int,
                      assessment_service: AssessmentService = Depends(),
                      user_id: str = Depends(get_current_user_id)):
    """Soft delete an assessment by ID.
    
    Args:
        assessment_id (int): ID of the assessment.
        assessment_service (AssessmentService): Service for assessment operations.
        user_id (str): ID of the current user.
        
    Returns:
        Response: HTTP 204 No Content response.
    """
    assessment_service.delete_assessment(assessment_id, user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
