"""Routes for managing sections."""

from fastapi import APIRouter, Depends, Response, status

from app.auth.auth_utils import get_current_user_id
from app.schemas.section import SectionCreate, SectionRead, SectionUpdate
from app.services.section import SectionService

router = APIRouter(prefix="/sections", tags=["sections"])

@router.get("/{semester_id}/{course_id}", response_model=list[SectionRead])
def read_sections(semester_id: int, course_id: int,
                  section_service: SectionService = Depends(),
                  user_id: str = Depends(get_current_user_id)):
    """Get all sections for a specific course in a semester.

    Args:
        semester_id (int): ID of the semester.
        course_id (int): ID of the course.
        section_service (SectionService): Service for section operations.
        user_id (str): ID of the current user.

    Returns:
        list[SectionRead]: List of sections for the specified course and semester.
    """
    return section_service.get_all_sections(semester_id, course_id, user_id)

@router.post("/", response_model=SectionRead)
def add_section(section: SectionCreate, section_service: SectionService = Depends(),
                user_id: str = Depends(get_current_user_id)):
    """Create a new section.
    
    Args:
        section (SectionCreate): Section data.
        section_service (SectionService): Service for section operations.
        user_id (str): ID of the current user.
    
    Returns:
        SectionRead: The created section.
    """
    return section_service.create_section(section, user_id)

@router.get("/{section_id}", response_model=SectionRead)
def read_section(section_id: int, section_service: SectionService = Depends(),
                  user_id: str = Depends(get_current_user_id)):
    """Get a section by ID.
    
    Args:
        section_id (int): ID of the section.
        section_service (SectionService): Service for section operations.
        user_id (str): ID of the current user.
        
    Returns:
        SectionRead: The requested section.
    """
    return section_service.get_section(section_id, user_id)

@router.put("/{section_id}", response_model=SectionRead)
def update_section(section_id: int, updated_section: SectionUpdate,
                   section_service: SectionService = Depends(),
                   user_id: str = Depends(get_current_user_id)):
    """Update a section by ID.
    
    Args:
        section_id (int): ID of the section.
        updated_section (SectionCreate): Updated section data.
        section_service (SectionService): Service for section operations.
        user_id (str): ID of the current user.
        
    Returns:
        SectionRead: The updated section.
    """
    return section_service.update_section(section_id, user_id, updated_section)

@router.delete("/{section_id}", response_model=SectionRead)
def delete_section(section_id: int,
                   section_service: SectionService = Depends(),
                   user_id: str = Depends(get_current_user_id)):
    """Soft delete a section by ID.
    
    Args:
        section_id (int): ID of the section.
        section_service (SectionService): Service for section operations.
        user_id (str): ID of the current user.
        
    Returns:
        Response: HTTP 204 No Content response.
    """
    section_service.delete_section(section_id, user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
