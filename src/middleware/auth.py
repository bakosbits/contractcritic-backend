from functools import wraps
from flask import request, jsonify, g
from jose import jwt, JWTError
import os
import requests
import json
from typing import Optional, Dict, Any

class SupabaseAuth:
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.jwt_secret = None
        self._fetch_jwt_secret()
    
    def _fetch_jwt_secret(self):
        """Fetch JWT secret from Supabase"""
        try:
            # Try to get the JWT secret from environment variables
            # First try SUPABASE_JWT_SECRET, then fall back to JWT_SECRET_KEY
            self.jwt_secret = os.getenv("SUPABASE_JWT_SECRET") or os.getenv("JWT_SECRET_KEY")
            
            if not self.jwt_secret:
                print("Warning: No JWT secret found in environment variables")
                self.jwt_secret = "your-jwt-secret-here"  # Fallback for development
            else:
                print("JWT secret loaded successfully")
        except Exception as e:
            print(f"Warning: Could not fetch JWT secret: {e}")
            self.jwt_secret = "your-jwt-secret-here"  # Fallback for development
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token and return payload"""
        try:
            # Decode the JWT token
            payload = jwt.decode(
                token,
                self.jwt_secret,
                algorithms=["HS256"],
                audience="authenticated"
            )
            return payload
        except JWTError as e:
            print(f"JWT verification failed: {e}")
            return None
        except Exception as e:
            print(f"Token verification error: {e}")
            return None
    
    def extract_user_info(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Extract user information from JWT payload"""
        return {
            'user_id': payload.get('sub'),
            'email': payload.get('email'),
            'role': payload.get('role', 'authenticated'),
            'aud': payload.get('aud'),
            'exp': payload.get('exp')
        }

# Global auth instance
supabase_auth = SupabaseAuth()

def require_auth(f):
    """Decorator to require authentication for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'No authorization header provided'}), 401
        
        # Check if it's a Bearer token
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Invalid authorization header format'}), 401
        
        # Extract token
        token = auth_header.split(' ')[1]
        if not token:
            return jsonify({'error': 'No token provided'}), 401
        
        # Verify token
        payload = supabase_auth.verify_token(token)
        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        # Extract user info and store in Flask's g object
        user_info = supabase_auth.extract_user_info(payload)
        g.user_id = user_info['user_id']
        g.user_email = user_info['email']
        g.user_role = user_info['role']
        
        # Ensure user_id exists
        if not g.user_id:
            return jsonify({'error': 'Invalid token: missing user ID'}), 401
        
        return f(*args, **kwargs)
    
    return decorated_function

def get_current_user() -> Optional[Dict[str, Any]]:
    """Get current user info from Flask's g object"""
    if hasattr(g, 'user_id') and g.user_id:
        return {
            'user_id': g.user_id,
            'email': getattr(g, 'user_email', None),
            'role': getattr(g, 'user_role', 'authenticated')
        }
    return None

def require_admin(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user or user.get('role') != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    
    return decorated_function
