from typing import Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.security import verify_jwt_token
from app.core.exceptions import AuthenticationError

# Security scheme for JWT tokens
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    FastAPI dependency to get the current authenticated user.
    Extracts and validates JWT token from Authorization header.
    """
    try:
        token = credentials.credentials
        user_info = verify_jwt_token(token)
        return user_info
    except HTTPException:
        raise
    except Exception as e:
        raise AuthenticationError(f"Authentication failed: {str(e)}")


async def get_current_user_id(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> str:
    """
    FastAPI dependency to get the current user's ID.
    """
    return current_user["user_id"]


async def get_current_user_email(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> str:
    """
    FastAPI dependency to get the current user's email.
    """
    return current_user["email"]


async def require_admin(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    FastAPI dependency to require admin role.
    """
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


def get_jwt_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """
    FastAPI dependency to extract JWT token for service calls.
    """
    return credentials.credentials
