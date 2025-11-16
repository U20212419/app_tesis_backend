"""Main application file."""

import logging
import os
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.exceptions import AppException
from app.logging_config import setup_logging
from app.routes import (test,
                        semester,
                        course,
                        course_in_semester,
                        section,
                        assessment,
                        statistics,
                        video_processing)

# Load environment variables from .env file
env = os.getenv("ENV", "development")
if env == "production":
    load_dotenv(".env.production")
else:
    load_dotenv(".env.development")

setup_logging()

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Backend",
    version="1.0.0"
)

# Exception handlers
@app.exception_handler(AppException)
async def app_exception_handler(_request: Request, exc: AppException):
    """Handler for custom application exceptions."""
    if 400 <= exc.status_code < 500:
        logger.warning("Client error: %s - %s", exc.code, exc.message)
    else:
        logger.error("Server error: %s - %s", exc.code, exc.message, exc_info=True)

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.code,
            "message": exc.message
        }
    )

@app.exception_handler(Exception)
async def generic_exception_handler(_request: Request, exc: Exception):
    """Generic exception handler for unhandled exceptions."""
    logger.error("Unhandled exception: %s", exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "code": "ERR_UNKNOWN",
            "message": "Ha ocurrido un error inesperado."
        }
    )

# Register routes
API_PREFIX = "/api/v1"

app.include_router(test.router, prefix=API_PREFIX)
app.include_router(semester.router, prefix=API_PREFIX)
app.include_router(course.router, prefix=API_PREFIX)
app.include_router(course_in_semester.router, prefix=API_PREFIX)
app.include_router(section.router, prefix=API_PREFIX)
app.include_router(assessment.router, prefix=API_PREFIX)
app.include_router(statistics.router, prefix=API_PREFIX)
app.include_router(video_processing.router, prefix=API_PREFIX)
