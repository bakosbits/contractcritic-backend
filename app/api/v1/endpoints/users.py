from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
import logging

from app.api.deps import get_current_user, get_jwt_token
from app.services.supabase_client import supabase_service

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/profile", response_model=Dict[str, Any])
async def get_user_profile(
    current_user: Dict[str, Any] = Depends(get_current_user),
    jwt_token: str = Depends(get_jwt_token)
):
    """Retrieve user profile."""
    user_id = current_user.get('user_id')
    logger.info(f"Getting user profile for user_id: {user_id}")
    
    try:
        # Get user data from public.profiles table
        client = supabase_service.get_client(jwt_token)
        
        # Query the profiles table (RLS will ensure user can only access their own profile)
        response = client.table("profiles").select("*").eq("id", user_id).execute()
        
        if response.data and len(response.data) > 0:
            profile = response.data[0]
            
            # Return profile data
            profile_data = {
                'user_id': profile['id'],
                'first_name': profile.get('first_name'),
                'last_name': profile.get('last_name'),
                'email': profile.get('email'),
                'phone': profile.get('phone'),
                'created_at': profile.get('created_at'),
                'updated_at': profile.get('updated_at')
            }
            
            logger.info(f"Successfully retrieved user profile for user_id: {user_id}")
            return {"success": True, "data": profile_data}
        else:
            logger.warning(f"No profile found for user_id: {user_id}")
            # Return basic user data as fallback
            fallback_data = {
                'user_id': user_id,
                'first_name': None,
                'last_name': None,
                'email': current_user.get('email'),
                'phone': None
            }
            return {"success": True, "data": fallback_data}
            
    except Exception as e:
        logger.error(f"Error in get_user_profile for user_id: {user_id}. Error: {e}", exc_info=True)
        # Fallback to basic current_user data
        fallback_data = {
            'user_id': user_id,
            'first_name': None,
            'last_name': None,
            'email': current_user.get('email'),
            'phone': None
        }
        return {"success": True, "data": fallback_data}

@router.put("/profile", response_model=Dict[str, Any])
async def update_user_profile(
    profile_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user),
    jwt_token: str = Depends(get_jwt_token)
):
    """Update user profile."""
    user_id = current_user.get('user_id')
    logger.info(f"Updating user profile for user_id: {user_id}")
    
    try:
        # Update user profile in Supabase
        success = supabase_service.update_profile(
            user_id,
            profile_data,
            jwt_token
        )
        
        if not success:
            logger.error(f"Failed to update user profile for user_id: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update user profile"
            )
        
        logger.info(f"User profile updated successfully for user_id: {user_id}")
        return {"success": True, "message": "Profile updated successfully"}
        
    except Exception as e:
        logger.error(f"An unexpected error occurred while updating user profile for user_id: {user_id}. Error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while updating user profile"
        )

@router.get("/stats", response_model=Dict[str, Any])
async def get_user_stats(
    current_user: Dict[str, Any] = Depends(get_current_user),
    jwt_token: str = Depends(get_jwt_token)
):
    """Retrieve user statistics."""
    user_id = current_user.get('user_id')
    logger.info(f"Fetching user stats for user_id: {user_id}")
    
    try:
        # Get user stats from Supabase
        stats = supabase_service.get_user_stats(user_id, jwt_token)
        
        if stats is None:
            logger.error(f"Failed to fetch user stats for user_id: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch user statistics"
            )
        
        logger.info(f"User stats fetched successfully for user_id: {user_id}")
        return {"success": True, "data": stats}
        
    except Exception as e:
        logger.error(f"An unexpected error occurred while fetching user stats for user_id: {user_id}. Error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while fetching user statistics"
        )
