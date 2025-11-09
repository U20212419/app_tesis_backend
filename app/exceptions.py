"""Custom exceptions for the application."""

class AppException(Exception):
    """Base class for application-specific exceptions."""
    status_code: int = 500
    code: str = "ERR_UNKNOWN"
    message: str = "Ha ocurrido un error inesperado."

    def __init__(self, message: str | None = None, code: str | None = None):
        """Initialize the exception with optional custom message and code."""
        if message:
            self.message = message
        if code:
            self.code = code
        super().__init__(self.message)

class AuthException(AppException):
    """Exception raised for authentication errors."""
    status_code: int = 401
    code: str = "ERR_AUTHENTICATION"
    message: str = "Ha ocurrido un error de autenticación. Por favor, vuelva a ingresar."

class InvalidTokenException(AuthException):
    """Exception raised for invalid authentication tokens."""
    code: str = "ERR_INVALID_TOKEN"
    message: str = "El token de autenticación no es válido. Por favor, vuelva a ingresar."

class ExpiredTokenException(AuthException):
    """Exception raised for expired authentication tokens."""
    code: str = "ERR_EXPIRED_TOKEN"
    message: str = "El token de autenticación ha expirado. Por favor, vuelva a ingresar."

class RevokedTokenException(AuthException):
    """Exception raised for revoked authentication tokens."""
    code: str = "ERR_REVOKED_TOKEN"
    message: str = "El token de autenticación ha sido revocado. Por favor, vuelva a ingresar."

class ResourceNotFoundException(AppException):
    """Exception raised when a requested resource is not found."""
    status_code: int = 404
    code: str = "ERR_RESOURCE_NOT_FOUND"
    message: str = "El recurso solicitado no fue encontrado."

class CourseNotFoundException(ResourceNotFoundException):
    """Exception raised when a requested course is not found."""
    code: str = "ERR_COURSE_NOT_FOUND"
    message: str = "El curso solicitado no fue encontrado."

class SemesterNotFoundException(ResourceNotFoundException):
    """Exception raised when a requested semester is not found."""
    code: str = "ERR_SEMESTER_NOT_FOUND"
    message: str = "El semestre solicitado no fue encontrado."

class CourseInSemesterNotFoundException(ResourceNotFoundException):
    """Exception raised when a requested course in semester relation is not found."""
    code: str = "ERR_COURSE_IN_SEMESTER_NOT_FOUND"
    message: str = "El curso solicitado no fue encontrado en el semestre seleccionado."

class AssessmentNotFoundException(ResourceNotFoundException):
    """Exception raised when a requested assessment is not found."""
    code: str = "ERR_ASSESSMENT_NOT_FOUND"
    message: str = "La evaluación solicitada no fue encontrada."

class DuplicateResourceException(AppException):
    """Exception raised when attempting to create a duplicate resource."""
    status_code: int = 409
    code: str = "ERR_DUPLICATE_RESOURCE"
    message: str = "El recurso que se intenta crear ya existe."

class CourseCodeDuplicateException(DuplicateResourceException):
    """Exception raised when a course with the entered code already exists."""
    code: str = "ERR_COURSE_CODE_DUPLICATE"
    message: str = "Ya existe un curso con el código ingresado."

class SemesterKeyDuplicateException(DuplicateResourceException):
    """Exception raised when a semester with the entered key already exists."""
    code: str = "ERR_SEMESTER_KEY_DUPLICATE"
    message: str = "Ya existe un semestre con el año y número ingresados."

class CourseAlreadyInSemesterException(DuplicateResourceException):
    """Exception raised when attempting to add a course that is already in the semester."""
    code: str = "ERR_COURSE_ALREADY_IN_SEMESTER"
    message: str = "El curso ya ha sido añadido al semestre seleccionado."
