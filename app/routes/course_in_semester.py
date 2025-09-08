"""Routes for managing courses in a semester."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import get_db
from ..schemas.course_in_semester import CourseInSemesterCreate, CourseInSemesterRead
from ..crud.course_in_semester import (get_all_courses_in_semester,
                                       create_course_in_semester,
                                       get_course_in_semester)

router = APIRouter(prefix="/courses-in-semester", tags=["courses", "semesters"])

@router.get("/", response_model=list[CourseInSemesterRead])
def read_courses_in_semester(db: Session = Depends(get_db)):
    """Get all courses in a semester."""
    return get_all_courses_in_semester(db)

@router.post("/", response_model=CourseInSemesterRead)
def add_course_in_semester(course_in_semester: CourseInSemesterCreate, 
                           db: Session = Depends(get_db)):
    """Create a new course in a semester."""
    return create_course_in_semester(db, course_in_semester)

@router.get("/{semester_id}/{course_id}", response_model=CourseInSemesterRead)
def read_course_in_semester(semester_id: int, course_id: int, db: Session = Depends(get_db)):
    """Get a course in a semester by IDs."""
    db_course_in_semester = get_course_in_semester(db, semester_id, course_id)
    if not db_course_in_semester:
        raise HTTPException(status_code=404, detail="Course not found in the semester.")
    return db_course_in_semester
