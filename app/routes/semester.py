"""Routes for managing semesters."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import get_db
from ..schemas.semester import SemesterCreate, SemesterRead
from ..crud.semester import get_all_semesters, create_semester, get_semester

router = APIRouter(prefix="/semesters", tags=["semesters"])

@router.get("/", response_model=list[SemesterRead])
def read_semesters(db: Session = Depends(get_db)):
    """Get all semesters."""
    return get_all_semesters(db)

@router.post("/", response_model=SemesterRead)
def add_semester(semester: SemesterCreate, db: Session = Depends(get_db)):
    """Create a new semester."""
    return create_semester(db, semester)

@router.get("/{semester_id}", response_model=SemesterRead)
def read_semester(semester_id: int, db: Session = Depends(get_db)):
    """Get a semester by ID."""
    db_semester = get_semester(db, semester_id)
    if not db_semester:
        raise HTTPException(status_code=404, detail="Semester not found.")
    return db_semester
