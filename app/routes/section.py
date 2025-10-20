"""Routes for managing sections."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.auth_utils import get_current_user_id
from app.db import get_db
from app.schemas.section import SectionCreate, SectionRead
from app.services.section import get_all_sections, create_section, get_section

router = APIRouter(prefix="/sections", tags=["sections"])

@router.get("/", response_model=list[SectionRead])
def read_sections(db: Session = Depends(get_db),
                  user_id: str = Depends(get_current_user_id)):
    """Get all sections.
    
    Args:
        db (Session): Database session.
        user_id (str): ID of the current user.
        
    Returns:
        list[SectionRead]: List of sections for a specific user.
    """
    return get_all_sections(db, user_id)

@router.post("/", response_model=SectionRead)
def add_section(section: SectionCreate, db: Session = Depends(get_db),
                user_id: str = Depends(get_current_user_id)):
    """Create a new section.
    
    Args:
        section (SectionCreate): Section data.
        db (Session): Database session.
        user_id (str): ID of the current user.
    
    Returns:
        SectionRead: The created section.
    """
    return create_section(db, section, user_id)

@router.get("/{section_id}", response_model=SectionRead)
def read_ssection(section_id: int, db: Session = Depends(get_db),
                  user_id: str = Depends(get_current_user_id)):
    """Get a section by ID.
    
    Args:
        section_id (int): ID of the section.
        db (Session): Database session.
        user_id (str): ID of the current user.
        
    Returns:
        SectionRead: The requested section.
        
    Raises:
        HTTPException: If the section is not found.
    """
    db_section = get_section(db, section_id, user_id)
    if not db_section:
        raise HTTPException(status_code=404, detail="Section not found.")
    return db_section
