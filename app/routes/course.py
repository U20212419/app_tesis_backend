"""Routes for managing courses."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import get_db
from ..schemas.course import CourseCreate, CourseRead
from ..crud.course import get_all_courses, create_course, get_course

router = APIRouter(prefix="/courses", tags=["courses"])

@router.get("/", response_model=list[CourseRead])
def read_courses(db: Session = Depends(get_db)):
    """Get all courses."""
    return get_all_courses(db)

@router.post("/", response_model=CourseRead)
def add_course(course: CourseCreate, db: Session = Depends(get_db)):
    """Create a new course."""
    return create_course(db, course)

@router.get("/{course_id}", response_model=CourseRead)
def read_course(course_id: int, db: Session = Depends(get_db)):
    """Get a course by ID."""
    db_course = get_course(db, course_id)
    if not db_course:
        raise HTTPException(status_code=404, detail="Course not found.")
    return db_course
