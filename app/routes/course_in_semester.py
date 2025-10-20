"""Routes for managing courses in a semester."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.auth_utils import get_current_user_id
from app.db import get_db
from app.schemas.course_in_semester import CourseInSemesterCreate, CourseInSemesterRead
from app.services.course_in_semester import (get_all_courses_in_semester,
                                           create_course_in_semester,
                                           get_course_in_semester)

router = APIRouter(prefix="/courses-in-semester", tags=["courses", "semesters"])

@router.get("/", response_model=list[CourseInSemesterRead])
def read_courses_in_semester(db: Session = Depends(get_db),
                             user_id: str = Depends(get_current_user_id)):
    """Get all courses in a semester.
    
    Args:
        db (Session): Database session.
        user_id (str): ID of the current user.
        
    Returns:
        list[CourseInSemesterRead]: List of courses in semesters.
    """
    return get_all_courses_in_semester(db, user_id)

@router.post("/", response_model=CourseInSemesterRead)
def add_course_in_semester(course_in_semester: CourseInSemesterCreate, 
                           db: Session = Depends(get_db),
                           user_id: str = Depends(get_current_user_id)):
    """Create a new course in a semester.
    
    Args:
        course_in_semester (CourseInSemesterCreate): Course in semester data.
        db (Session): Database session.
        user_id (str): ID of the current user.
        
    Returns:
        CourseInSemesterRead: The created course in semester.
    """
    return create_course_in_semester(db, course_in_semester, user_id)

@router.get("/{semester_id}/{course_id}", response_model=CourseInSemesterRead)
def read_course_in_semester(semester_id: int, course_id: int, db: Session = Depends(get_db),
                            user_id: str = Depends(get_current_user_id)):
    """Get a course in a semester by IDs.
    
    Args:
        semester_id (int): ID of the semester.
        course_id (int): ID of the course.
        db (Session): Database session.
        user_id (str): ID of the current user.
        
    Returns:
        CourseInSemesterRead: The requested course in semester.
        
    Raises:
        HTTPException: If the course in semester is not found.
    """
    db_course_in_semester = get_course_in_semester(db, semester_id, course_id, user_id)
    if not db_course_in_semester:
        raise HTTPException(status_code=404, detail="Course not found in the semester.")
    return db_course_in_semester
