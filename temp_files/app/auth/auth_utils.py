from fastapi import Request, HTTPException, Depends
from fastapi.responses import RedirectResponse
from app.auth.supabase_auth import supabase
import logging
from typing import Optional
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

async def get_current_user(request: Request):
    """Get the currently logged in user from the request"""
    try:
        # Get the session token from cookies
        access_token = request.cookies.get("access_token") or request.cookies.get("sb-access-token")
        
        if not access_token:
            logger.warning("No access token found in cookies")
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        # Verify the token and get the user
        user = await verify_token(access_token)
        if not user:
            logger.warning("Invalid access token")
            raise HTTPException(status_code=401, detail="Invalid token")
        
        return user
    except Exception as e:
        logger.error(f"Error getting current user: {str(e)}")
        # Add the stack trace for better debugging
        import traceback
        logger.error(f"Stack trace: {traceback.format_exc()}")
        raise HTTPException(status_code=401, detail="Authentication error")

async def verify_token(access_token: str):
    """Verify a user token and return the user"""
    try:
        # Use Supabase to verify the token
        user_response = supabase.auth.get_user(access_token)
        if not user_response or not user_response.user:
            return None
        return user_response.user
    except Exception as e:
        logger.error(f"Error verifying token: {str(e)}")
        
        # Check if token is expired and try to refresh
        if "token is expired" in str(e).lower():
            # Logic to handle token refresh could go here
            # This would require the refresh token
            pass
        
        return None

def set_auth_cookies(response, session):
    """Set auth cookies on the response"""
    # Make sure we have valid tokens
    if not session or not session.access_token:
        return response
    
    # Set both cookie names to ensure compatibility
    cookie_settings = {
        "httponly": True,
        "secure": settings.ENV != "development",  # Only secure in production
        "samesite": "lax",
        "max_age": 3600,  # 1 hour
    }
    
    response.set_cookie(key="access_token", value=session.access_token, **cookie_settings)
    response.set_cookie(key="sb-access-token", value=session.access_token, **cookie_settings)
    
    if session.refresh_token:
        refresh_settings = cookie_settings.copy()
        refresh_settings["max_age"] = 7 * 24 * 3600  # 7 days
        response.set_cookie(key="refresh_token", value=session.refresh_token, **refresh_settings)
        response.set_cookie(key="sb-refresh-token", value=session.refresh_token, **refresh_settings)
    
    return response

def clear_auth_cookies(response):
    """Clear authentication cookies from a response object"""
    response.delete_cookie(key="access_token")
    response.delete_cookie(key="refresh_token")
    return response 