"""CRUD operations for the Assessment model."""

from sqlalchemy.orm import Session
from ..models.assessment import Assessment
from ..schemas.assessment import AssessmentCreate

def get_all_assessments(db: Session):
    """Retrieve all assessments from the database."""
    return db.query(Assessment).all()

def get_assessment(db: Session, assessment_id: int):
    """Retrieve a specific assessment by its ID."""
    return db.query(Assessment).filter(Assessment.id_assessment == assessment_id).first()

def create_assessment(db: Session, assessment: AssessmentCreate):
    """Create a new assessment in the database."""
    db_assessment = Assessment(**assessment.model_dump())
    db.add(db_assessment)
    db.commit()
    db.refresh(db_assessment)
    return db_assessment
