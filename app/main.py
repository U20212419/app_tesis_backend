"""Main application file."""

import os
from fastapi import FastAPI
from dotenv import load_dotenv
from app.routes import test

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
