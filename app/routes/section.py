"""Routes for managing sections."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import get_db
from ..schemas.section import SectionCreate, SectionRead
from ..crud.section import get_all_sections, create_section, get_section

router = APIRouter(prefix="/sections", tags=["sections"])

@router.get("/", response_model=list[SectionRead])
def read_sections(db: Session = Depends(get_db)):
    """Get all sections."""
    return get_all_sections(db)

@router.post("/", response_model=SectionRead)
def add_section(section: SectionCreate, db: Session = Depends(get_db)):
    """Create a new section."""
    return create_section(db, section)

@router.get("/{section_id}", response_model=SectionRead)
def read_ssection(section_id: int, db: Session = Depends(get_db)):
    """Get a section by ID."""
    db_section = get_section(db, section_id)
    if not db_section:
        raise HTTPException(status_code=404, detail="Section not found.")
    return db_section
