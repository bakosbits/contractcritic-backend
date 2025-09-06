from flask import Blueprint, jsonify, request, g
from src.middleware.auth import require_auth, get_current_user
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

user_bp = Blueprint('user', __name__)

@user_bp.route('/user/profile', methods=['GET'])
@require_auth
def get_user_profile():
    """
    Get the current authenticated user's profile information.
    This information comes from the JWT token provided by Supabase Auth.
    """
    try:
        user_info = get_current_user()
        
        if not user_info:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
        
        return jsonify({
            'success': True,
            'data': {
                'user_id': user_info['user_id'],
                'email': user_info['email'],
                'role': user_info['role']
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching user profile: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@user_bp.route('/user/preferences', methods=['GET'])
@require_auth
def get_user_preferences():
    """
    Get user preferences (placeholder for future implementation).
    In a full implementation, this would fetch user preferences from Supabase.
    """
    try:
        # For now, return default preferences
        # In the future, this could be stored in a user_preferences table
        default_preferences = {
            'theme': 'light',
            'notifications': True,
            'default_analysis_type': 'small_business',
            'language': 'en'
        }
        
        return jsonify({
            'success': True,
            'data': default_preferences
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching user preferences: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@user_bp.route('/user/preferences', methods=['PUT'])
@require_auth
def update_user_preferences():
    """
    Update user preferences (placeholder for future implementation).
    In a full implementation, this would update user preferences in Supabase.
    """
    try:
        data = request.get_json() or {}
        
        # Validate preference keys
        allowed_preferences = ['theme', 'notifications', 'default_analysis_type', 'language']
        preferences = {}
        
        for key, value in data.items():
            if key in allowed_preferences:
                preferences[key] = value
        
        # For now, just return success
        # In the future, this would save to a user_preferences table
        logger.info(f"User {g.user_id} updated preferences: {preferences}")
        
        return jsonify({
            'success': True,
            'data': preferences,
            'message': 'Preferences updated successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Error updating user preferences: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@user_bp.route('/auth/verify', methods=['GET'])
@require_auth
def verify_auth():
    """
    Verify that the user's authentication token is valid.
    This endpoint can be used by the frontend to check if the user is still authenticated.
    """
    try:
        user_info = get_current_user()
        
        return jsonify({
            'success': True,
            'data': {
                'authenticated': True,
                'user_id': user_info['user_id'],
                'email': user_info['email'],
                'role': user_info['role']
            },
            'message': 'Authentication valid'
        }), 200
        
    except Exception as e:
        logger.error(f"Error verifying authentication: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Authentication verification failed'
        }), 401

# Note: User registration, login, logout, and password management are now handled by Supabase Auth
# These endpoints are no longer needed as they're handled by the frontend Supabase client:
# - POST /auth/register (handled by supabase.auth.signUp)
# - POST /auth/login (handled by supabase.auth.signInWithPassword)
# - POST /auth/logout (handled by supabase.auth.signOut)
# - POST /auth/reset-password (handled by supabase.auth.resetPasswordForEmail)
# - OAuth providers (handled by supabase.auth.signInWithOAuth)

@user_bp.route('/auth/info', methods=['GET'])
def get_auth_info():
    """
    Get information about available authentication methods.
    This is a public endpoint that doesn't require authentication.
    """
    try:
        return jsonify({
            'success': True,
            'data': {
                'auth_methods': {
                    'email_password': True,
                    'oauth_providers': ['google', 'github', 'azure']
                },
                'features': {
                    'email_verification': True,
                    'password_reset': True,
                    'social_login': True
                },
                'message': 'Authentication is handled by Supabase Auth. Use the frontend client for login/registration.'
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting auth info: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500
