"""Main application file."""

import os
from fastapi import FastAPI
from dotenv import load_dotenv
from app.routes import (test,
                        semester,
                        course,
                        course_in_semester,
                        section,
                        assessment)

# Load environment variables from .env file
env = os.getenv("ENV", "development")
if env == "production":
    load_dotenv(".env.production")
else:
    load_dotenv(".env.development")

app = FastAPI(
    title="Backend",
    version="1.0.0"
)

# Register routes
app.include_router(test.router)
app.include_router(semester.router)
app.include_router(course.router)
app.include_router(course_in_semester.router)
app.include_router(section.router)
app.include_router(assessment.router)
