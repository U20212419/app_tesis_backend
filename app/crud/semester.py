"""CRUD operations for the Semester model."""

from sqlalchemy.orm import Session
from ..models.semester import Semester
from ..schemas.semester import SemesterCreate

def get_all_semesters(db: Session):
    """Retrieve all semesters from the database."""
    return db.query(Semester).all()

def get_semester(db: Session, semester_id: int):
    """Retrieve a specific semester by its ID."""
    return db.query(Semester).filter(Semester.id_semester == semester_id).first()

def create_semester(db: Session, semester: SemesterCreate):
    """Create a new semester in the database."""
    db_semester = Semester(**semester.dict())
    db.add(db_semester)
    db.commit()
    db.refresh(db_semester)
    return db_semester
