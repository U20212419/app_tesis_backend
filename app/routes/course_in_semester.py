"""Routes for managing courses in a semester."""

from fastapi import APIRouter, Depends, Response, status

from app.auth.auth_utils import get_current_user_id
from app.schemas.course_in_semester import CourseInSemesterRead
from app.services.course_in_semester import CourseInSemesterService

router = APIRouter(prefix="/courses-in-semester", tags=["courses", "semesters"])

@router.get("/", response_model=list[CourseInSemesterRead])
def read_courses_in_semesters(course_in_semester_service: CourseInSemesterService = Depends(),
                              user_id: str = Depends(get_current_user_id)):
    """Get all courses in all semesters.
    
    Args:
        course_in_semester_service (CourseInSemesterService): Service for
            course in semester operations.
        user_id (str): ID of the current user.
        
    Returns:
        list[CourseInSemesterRead]: List of courses in semesters.
    """
    return course_in_semester_service.get_all_courses_in_semesters(user_id)

@router.get("/{semester_id}", response_model=list[CourseInSemesterRead])
def read_courses_in_semester(semester_id: int,
                             course_in_semester_service: CourseInSemesterService = Depends(),
                             user_id: str = Depends(get_current_user_id)):
    """Get all courses in a specific semester.
    
    Args:
        semester_id (int): ID of the semester.
        course_in_semester_service (CourseInSemesterService): Service for
            course in semester operations.
        user_id (str): ID of the current user.
        
    Returns:
        list[CourseInSemesterRead]: List of courses in the specified semester.
    """
    return course_in_semester_service.get_all_courses_in_semester(semester_id, user_id)

@router.get("/{semester_id}/{course_id}", response_model=CourseInSemesterRead)
def read_course_in_semester(semester_id: int, course_id: int,
                            course_in_semester_service: CourseInSemesterService = Depends(),
                            user_id: str = Depends(get_current_user_id)):
    """Get a course in a semester by IDs.
    
    Args:
        semester_id (int): ID of the semester.
        course_id (int): ID of the course.
        course_in_semester_service (CourseInSemesterService): Service for course in semester
        user_id (str): ID of the current user.
        
    Returns:
        CourseInSemesterRead: The requested course in semester.
        
    Raises:
        HTTPException: If the course in semester is not found.
    """
    return course_in_semester_service.get_course_in_semester(
        semester_id,
        course_id,
        user_id
    )

@router.post("/{semester_id}/{course_id}", response_model=CourseInSemesterRead)
def add_course_to_semester(semester_id: int, course_id: int,
                           course_in_semester_service: CourseInSemesterService = Depends(),
                           user_id: str = Depends(get_current_user_id)):
    """Add a course to a semester.

    Args:
        semester_id (int): ID of the semester.
        course_id (int): ID of the course.
        course_in_semester_service (CourseInSemesterService): Service for
            course in semester operations.
        user_id (str): ID of the current user.

    Returns:
        CourseInSemesterRead: The course added to the semester.
    """
    return course_in_semester_service.add_course_to_semester(semester_id, course_id, user_id)

@router.delete("/{semester_id}/{course_id}", response_model=dict)
def remove_course_from_semester(semester_id: int, course_id: int,
                                course_in_semester_service: CourseInSemesterService = Depends(),
                                user_id: str = Depends(get_current_user_id)):
    """Remove a course from a semester.
    
    Args:
        semester_id (int): ID of the semester.
        course_id (int): ID of the course.
        course_in_semester_service (CourseInSemesterService): Service for course in semester
        user_id (str): ID of the current user.

    Returns:
        Response: HTTP 204 No Content response.

    Raises:
        HTTPException: If the course is not found in the semester.
    """
    course_in_semester_service.remove_course_from_semester(
        semester_id,
        course_id,
        user_id
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
