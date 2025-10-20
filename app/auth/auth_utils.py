"""Utility functions for authentication and user management."""

import os
from pathlib import Path
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import firebase_admin
from firebase_admin import auth, credentials

cred_env = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
if not cred_env:
    raise RuntimeError("Set GOOGLE_APPLICATION_CREDENTIALS in your .env")

cred_path = Path(os.path.expanduser(cred_env)).resolve()

cred = credentials.Certificate(cred_path)
firebase_admin.initialize_app(cred)
security = HTTPBearer()

def get_current_user_id(token: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Retrieves the current user's ID from the provided authentication token.

    Args:
        token (HTTPAuthorizationCredentials): The authorization credentials containing the token.

    Returns:
        str: The user ID extracted from the token.

    Raises:
        HTTPException: If the token is invalid or verification fails.
    """
    try:
        decoded_token = auth.verify_id_token(token.credentials)
        return decoded_token["uid"]
    except Exception as exc:
        print(f"Token verification failed: {exc}")
        raise HTTPException(status_code=401, detail="Invalid authentication token.") from exc
