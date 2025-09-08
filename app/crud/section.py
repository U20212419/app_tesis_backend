"""CRUD operations for the Section model."""

from sqlalchemy.orm import Session
from ..models.section import Section
from ..schemas.section import SectionCreate

def get_all_sections(db: Session):
    """Retrieve all sections from the database."""
    return db.query(Section).all()

def get_section(db: Session, section_id: int):
    """Retrieve a specific section by its ID."""
    return db.query(Section).filter(Section.id_section == section_id).first()

def create_section(db: Session, section: SectionCreate):
    """Create a new section in the database."""
    db_section = Section(**section.model_dump())
    db.add(db_section)
    db.commit()
    db.refresh(db_section)
    return db_section
