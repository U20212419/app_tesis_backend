"""Routes for managing semesters."""

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.auth.auth_utils import get_current_user_id
from app.schemas.semester import SemesterCreate, SemesterRead
from app.services.semester import SemesterService

router = APIRouter(prefix="/semesters", tags=["semesters"])

@router.get("/", response_model=list[SemesterRead])
def read_semesters(semester_service: SemesterService = Depends(),
                   user_id: str = Depends(get_current_user_id)):
    """Get all semesters.
    
    Args:
        semester_service (SemesterService): Service for semester operations.
        user_id (str): ID of the current user.
        
    Returns:
        list[SemesterRead]: List of semesters for a specific user.
    """
    return semester_service.get_all_semesters(user_id)

@router.post("/", response_model=SemesterRead)
def add_semester(semester: SemesterCreate, semester_service: SemesterService = Depends(),
                 user_id: str = Depends(get_current_user_id)):
    """Create a new semester.
    
    Args:
        semester (SemesterCreate): Semester data.
        semester_service (SemesterService): Service for semester operations.
        user_id (str): ID of the current user.
        
    Returns:
        SemesterRead: The created semester.
    """
    return semester_service.create_semester(semester, user_id)

@router.get("/detailed", response_model=list[SemesterRead])
def read_semesters_detailed(semester_service: SemesterService = Depends(),
                            user_id: str = Depends(get_current_user_id)):
    """Get all semesters, including the amount 
    of courses that are present in each semester.
    
    Args:
        semester_service (SemesterService): Service for semester operations.
        user_id (str): ID of the current user.
        
    Returns:
        list[SemesterRead]: List of semesters for a specific user.
    """
    return semester_service.get_all_semesters_detailed(user_id)

@router.get("/{semester_id}", response_model=SemesterRead)
def read_semester(semester_id: int, semester_service: SemesterService = Depends(),
                  user_id: str = Depends(get_current_user_id)):
    """Get a semester by ID.
    
    Args:
        semester_id (int): ID of the semester.
        semester_service (SemesterService): Service for semester operations.
        user_id (str): ID of the current user.
        
    Returns:
        SemesterRead: The requested semester.
        
    Raises:
        HTTPException: If the semester is not found.
    """
    db_semester = semester_service.get_semester(semester_id, user_id)
    if not db_semester:
        raise HTTPException(status_code=404, detail="Semester not found.")
    return db_semester

@router.put("/{semester_id}", response_model=SemesterRead)
def update_semester(semester_id: int, updated_semester: SemesterCreate,
                    semester_service: SemesterService = Depends(),
                    user_id: str = Depends(get_current_user_id)):
    """Update a semester by ID.

    Args:
        semester_id (int): ID of the semester.
        updated_semester (SemesterCreate): Updated semester data.
        semester_service (SemesterService): Service for semester operations.
        user_id (str): ID of the current user.
        
    Returns:
        SemesterRead: The updated semester.
    
    Raises:
        HTTPException: If the semester is not found.
    """
    db_semester = semester_service.update_semester(semester_id, user_id, updated_semester)
    if not db_semester:
        raise HTTPException(status_code=404, detail="Semester not found.")
    return db_semester

@router.delete("/{semester_id}", response_model=SemesterRead)
def delete_semester(semester_id: int, semester_service: SemesterService = Depends(),
                    user_id: str = Depends(get_current_user_id)):
    """Soft delete a semester by ID.
    
    Args:
        semester_id (int): ID of the semester.
        semester_service (SemesterService): Service for semester operations.
        user_id (str): ID of the current user.
        
    Returns:
        Response: HTTP 204 No Content response.
    
    Raises:
        HTTPException: If the semester is not found.
    """
    db_semester = semester_service.delete_semester(semester_id, user_id)
    if not db_semester:
        raise HTTPException(status_code=404, detail="Semester not found.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
