"""Test routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.db import get_db

router = APIRouter()

@router.get("/health")
def health():
    """Health check endpoint.
    
    Returns:
        dict: A dictionary indicating the service status.
    """
    return {"status": "OK"}

@router.get("/test-db")
def test_db(db: Session = Depends(get_db)):
    """Test database connection.
    
    Args:
        db (Session): Database session.
    
    Returns:
        dict: A dictionary with the current server time from the database.
    """
    result = db.execute(text("SELECT NOW()"))
    server_time = result.fetchone()
    return {"server_time": str(server_time[0]) if server_time else None}
