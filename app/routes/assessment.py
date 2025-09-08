"""Routes for managing assessments."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import get_db
from ..schemas.assessment import AssessmentCreate, AssessmentRead
from ..crud.assessment import get_all_assessments, create_assessment, get_assessment

router = APIRouter(prefix="/assessments", tags=["assessments"])

@router.get("/", response_model=list[AssessmentRead])
def read_assessments(db: Session = Depends(get_db)):
    """Get all assessments."""
    return get_all_assessments(db)

@router.post("/", response_model=AssessmentRead)
def add_assessment(assessment: AssessmentCreate, db: Session = Depends(get_db)):
    """Create a new assessment."""
    return create_assessment(db, assessment)

@router.get("/{assessment_id}", response_model=AssessmentRead)
def read_assessment(assessment_id: int, db: Session = Depends(get_db)):
    """Get an assessment by ID."""
    db_assessment = get_assessment(db, assessment_id)
    if not db_assessment:
        raise HTTPException(status_code=404, detail="Assessment not found.")
    return db_assessment
