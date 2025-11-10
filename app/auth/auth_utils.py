"""Utility functions for authentication and user management."""

import logging
import os
from pathlib import Path
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import firebase_admin
from firebase_admin import auth, credentials

from app.exceptions import (
    AppException,
    InvalidTokenException,
    ExpiredTokenException,
    RevokedTokenException
)

cred_env = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
if not cred_env:
    raise RuntimeError("Set GOOGLE_APPLICATION_CREDENTIALS in your .env")

cred_path = Path(os.path.expanduser(cred_env)).resolve()

cred = credentials.Certificate(cred_path)
firebase_admin.initialize_app(cred)
security = HTTPBearer()

logger = logging.getLogger(__name__)

def get_current_user_id(token: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Retrieves the current user's ID from the provided authentication token.

    Args:
        token (HTTPAuthorizationCredentials): The authorization credentials containing the token.

    Returns:
        str: The user ID extracted from the token.

    Raises:
        ExpiredTokenException: If the token has expired.
        RevokedTokenException: If the token has been revoked.
        InvalidTokenException: If the token is invalid.
        AppException: For any other unexpected errors during token verification.
    """
    try:
        decoded_token = auth.verify_id_token(
            token.credentials,
            clock_skew_seconds=60  # Allow 1 minute clock skew for token validation
        )
        return decoded_token["uid"]
    except auth.ExpiredIdTokenError as e:
        logger.warning("Attempted access with an expired token: %s", e)
        raise ExpiredTokenException() from e
    except auth.RevokedIdTokenError as e:
        logger.warning("Attempted access with a revoked token: %s", e)
        raise RevokedTokenException() from e
    except (auth.InvalidIdTokenError, ValueError) as e:
        logger.warning("Attempted access with an invalid token: %s", e)
        raise InvalidTokenException() from e
    except Exception as e:
        logger.error("Unexpected error during token verification: %s", e, exc_info=True)
        raise AppException() from e
