"""Routes for managing courses."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.auth_utils import get_current_user_id
from app.db import get_db
from app.schemas.course import CourseCreate, CourseRead
from app.services.course import get_all_courses, create_course, get_all_courses_detailed, get_course

router = APIRouter(prefix="/courses", tags=["courses"])

@router.get("/", response_model=list[CourseRead])
def read_courses(db: Session = Depends(get_db),
                 user_id: str = Depends(get_current_user_id)):
    """Get all courses.
    
    Args:
        db (Session): Database session.
        user_id (str): ID of the current user.
        
    Returns:
        list[CourseRead]: List of courses for a specific user.
    """
    return get_all_courses(db, user_id)

@router.post("/", response_model=CourseRead)
def add_course(course: CourseCreate, db: Session = Depends(get_db),
               user_id: str = Depends(get_current_user_id)):
    """Create a new course.
    
    Args:
        course (CourseCreate): Course data.
        db (Session): Database session.
        user_id (str): ID of the current user.
        
    Returns:
        CourseRead: The created course.
    """
    return create_course(db, course, user_id)

@router.get("/detailed", response_model=list[CourseRead])
def read_courses_detailed(db: Session = Depends(get_db),
                          user_id: str = Depends(get_current_user_id)):
    """Get all courses, including the amount 
    of semesters in which each course is present.
    
    Args:
        db (Session): Database session.
        user_id (str): ID of the current user.
        
    Returns:
        list[CourseRead]: List of courses for a specific user.
    """
    return get_all_courses_detailed(db, user_id)

@router.get("/{course_id}", response_model=CourseRead)
def read_course(course_id: int, db: Session = Depends(get_db),
                user_id: str = Depends(get_current_user_id)):
    """Get a course by ID.
    
    Args:
        course_id (int): ID of the course.
        db (Session): Database session.
        user_id (str): ID of the current user.
        
    Returns:
        CourseRead: The requested course.
    
    Raises:
        HTTPException: If the course is not found.
    """
    db_course = get_course(db, course_id, user_id)
    if not db_course:
        raise HTTPException(status_code=404, detail="Course not found.")
    return db_course
