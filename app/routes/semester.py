"""Routes for managing semesters."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.auth_utils import get_current_user_id
from app.db import get_db
from app.schemas.semester import SemesterCreate, SemesterRead
from app.services.semester import get_all_semesters, create_semester, get_all_semesters_detailed, get_semester

router = APIRouter(prefix="/semesters", tags=["semesters"])

@router.get("/", response_model=list[SemesterRead])
def read_semesters(db: Session = Depends(get_db),
                   user_id: str = Depends(get_current_user_id)):
    """Get all semesters.
    
    Args:
        db (Session): Database session.
        user_id (str): ID of the current user.
        
    Returns:
        list[SemesterRead]: List of semesters for a specific user.
    """
    return get_all_semesters(db, user_id)

@router.post("/", response_model=SemesterRead)
def add_semester(semester: SemesterCreate, db: Session = Depends(get_db),
                 user_id: str = Depends(get_current_user_id)):
    """Create a new semester.
    
    Args:
        semester (SemesterCreate): Semester data.
        db (Session): Database session.
        user_id (str): ID of the current user.
        
    Returns:
        SemesterRead: The created semester.
    """
    return create_semester(db, semester, user_id)

@router.get("/detailed", response_model=list[SemesterRead])
def read_semesters_detailed(db: Session = Depends(get_db),
                            user_id: str = Depends(get_current_user_id)):
    """Get all semesters, including the amount 
    of courses that are present in each semester.
    
    Args:
        db (Session): Database session.
        user_id (str): ID of the current user.
        
    Returns:
        list[SemesterRead]: List of semesters for a specific user.
    """
    return get_all_semesters_detailed(db, user_id)

@router.get("/{semester_id}", response_model=SemesterRead)
def read_semester(semester_id: int, db: Session = Depends(get_db),
                  user_id: str = Depends(get_current_user_id)):
    """Get a semester by ID.
    
    Args:
        semester_id (int): ID of the semester.
        db (Session): Database session.
        user_id (str): ID of the current user.
        
    Returns:
        SemesterRead: The requested semester.
        
    Raises:
        HTTPException: If the semester is not found.
    """
    db_semester = get_semester(db, semester_id, user_id)
    if not db_semester:
        raise HTTPException(status_code=404, detail="Semester not found.")
    return db_semester
