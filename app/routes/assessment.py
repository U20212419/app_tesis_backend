"""Routes for managing assessments."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.auth_utils import get_current_user_id
from app.db import get_db
from app.schemas.assessment import AssessmentCreate, AssessmentRead
from app.services.assessment import get_all_assessments, create_assessment, get_assessment

router = APIRouter(prefix="/assessments", tags=["assessments"])

@router.get("/", response_model=list[AssessmentRead])
def read_assessments(db: Session = Depends(get_db),
                     user_id: str = Depends(get_current_user_id)):
    """Get all assessments.
    
    Args:
        db (Session): Database session.
        user_id (str): ID of the current user.

    Returns:
        list[AssessmentRead]: List of assessments for a specific user.
    """
    return get_all_assessments(db, user_id)

@router.post("/", response_model=AssessmentRead)
def add_assessment(assessment: AssessmentCreate, db: Session = Depends(get_db),
                   user_id: str = Depends(get_current_user_id)):
    """Create a new assessment.
    
    Args:
        assessment (AssessmentCreate): Assessment data.
        db (Session): Database session.
        user_id (str): ID of the current user.
        
    Returns:
        AssessmentRead: The created assessment.
    """
    return create_assessment(db, assessment, user_id)

@router.get("/{assessment_id}", response_model=AssessmentRead)
def read_assessment(assessment_id: int, db: Session = Depends(get_db),
                    user_id: str = Depends(get_current_user_id)):
    """Get an assessment by ID.
    
    Args:
        assessment_id (int): ID of the assessment.
        db (Session): Database session.
        user_id (str): ID of the current user.
        
    Returns:
        AssessmentRead: The requested assessment.

    Raises:
        HTTPException: If the assessment is not found.
    """
    db_assessment = get_assessment(db, assessment_id, user_id)
    if not db_assessment:
        raise HTTPException(status_code=404, detail="Assessment not found.")
    return db_assessment
