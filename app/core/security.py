from typing import Optional, Dict, Any
import logging
from fastapi import HTTPException, status
from jose import jwt, JWTError
from app.core.config import settings

logger = logging.getLogger(__name__)


class SupabaseAuth:
    """Supabase JWT authentication handler for FastAPI."""
    
    def __init__(self):
        self.jwt_secret = settings.supabase_jwt_secret or settings.secret_key
        logger.info(f"Initializing SupabaseAuth with JWT secret present: {bool(self.jwt_secret)}")
        logger.info(f"Using supabase_jwt_secret: {bool(settings.supabase_jwt_secret)}")
        if not self.jwt_secret:
            logger.error("JWT secret must be configured")
            raise ValueError("JWT secret must be configured")
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token and return payload."""
        logger.debug(f"Attempting to verify JWT token (length: {len(token) if token else 0})")
        try:
            # Decode the JWT token
            payload = jwt.decode(
                token,
                self.jwt_secret,
                algorithms=["HS256"],
                audience="authenticated"
            )
            logger.info(f"JWT token verified successfully for user: {payload.get('sub', 'unknown')}")
            return payload
        except JWTError as e:
            logger.error(f"JWT verification failed: {e}")
            logger.debug(f"Token that failed: {token[:50]}..." if token and len(token) > 50 else token)
            return None
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            return None
    
    def extract_user_info(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Extract user information from JWT payload."""
        return {
            'user_id': payload.get('sub'),
            'email': payload.get('email'),
            'role': payload.get('role', 'authenticated'),
            'aud': payload.get('aud'),
            'exp': payload.get('exp')
        }


# Global auth instance
supabase_auth = SupabaseAuth()


def verify_jwt_token(token: str) -> Dict[str, Any]:
    """
    Verify JWT token and return user information.
    Raises HTTPException if token is invalid.
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No token provided"
        )
    
    # Verify token
    payload = supabase_auth.verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    # Extract user info
    user_info = supabase_auth.extract_user_info(payload)
    
    # Ensure user_id exists
    if not user_info.get('user_id'):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing user ID"
        )
    
    return user_info
