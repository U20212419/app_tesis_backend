"""Routes for managing courses."""

from fastapi import APIRouter, Depends, Response, status

from app.auth.auth_utils import get_current_user_id
from app.schemas.course import CourseCreate, CourseRead
from app.services.course import CourseService

router = APIRouter(prefix="/courses", tags=["courses"])

@router.get("/", response_model=list[CourseRead])
def read_courses(course_service: CourseService = Depends(),
                 user_id: str = Depends(get_current_user_id)):
    """Get all courses.
    
    Args:
        course_service (CourseService): Service for course operations.
        user_id (str): ID of the current user.
        
    Returns:
        list[CourseRead]: List of courses for a specific user.
    """
    return course_service.get_all_courses(user_id)

@router.post("/", response_model=CourseRead)
def add_course(course: CourseCreate, course_service: CourseService = Depends(),
               user_id: str = Depends(get_current_user_id)):
    """Create a new course.
    
    Args:
        course (CourseCreate): Course data.
        course_service (CourseService): Service for course operations.
        user_id (str): ID of the current user.
        
    Returns:
        CourseRead: The created course.
    """
    return course_service.create_course(course, user_id)

@router.get("/detailed", response_model=list[CourseRead])
def read_courses_detailed(course_service: CourseService = Depends(),
                          user_id: str = Depends(get_current_user_id)):
    """Get all courses, including the amount
    of semesters in which each course is present.
    
    Args:
        course_service (CourseService): Service for course operations.
        user_id (str): ID of the current user.
        
    Returns:
        list[CourseRead]: List of courses for a specific user.
    """
    return course_service.get_all_courses_detailed(user_id)

@router.get("/{course_id}", response_model=CourseRead)
def read_course(course_id: int, course_service: CourseService = Depends(),
                user_id: str = Depends(get_current_user_id)):
    """Get a course by ID.
    
    Args:
        course_id (int): ID of the course.
        course_service (CourseService): Service for course operations.
        user_id (str): ID of the current user.
        
    Returns:
        CourseRead: The requested course.
    
    Raises:
        HTTPException: If the course is not found.
    """
    return course_service.get_course(course_id, user_id)

@router.put("/{course_id}", response_model=CourseRead)
def update_course(course_id: int, updated_course: CourseCreate,
                  course_service: CourseService = Depends(),
                  user_id: str = Depends(get_current_user_id)):
    """Update a course by ID.
    
    Args:
        course_id (int): ID of the course.
        updated_course (CourseCreate): Updated course data.
        course_service (CourseService): Service for course operations.
        user_id (str): ID of the current user.
        
    Returns:
        CourseRead: The updated course.
    
    Raises:
        HTTPException: If the course is not found.
    """
    return course_service.update_course(course_id, user_id, updated_course)

@router.delete("/{course_id}", response_model=CourseRead)
def delete_course(course_id: int, course_service: CourseService = Depends(),
                  user_id: str = Depends(get_current_user_id)):
    """Soft delete a course by ID.

    Args:
        course_id (int): ID of the course.
        course_service (CourseService): Service for course operations.
        user_id (str): ID of the current user.

    Returns:
        Response: HTTP 204 No Content response.
        
    Raises:
        HTTPException: If the course is not found.
    """
    course_service.delete_course(course_id, user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
