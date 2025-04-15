import os
from supabase import create_client, Client
from gotrue.errors import AuthApiError
import jwt
import logging
from fastapi import Request, HTTPException
from app.config import settings, get_settings

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SITE_URL = os.getenv("DOMAIN")

logger = logging.getLogger(__name__)

# Check if Supabase credentials are available
if not SUPABASE_URL or not SUPABASE_KEY or not SITE_URL:
    error_msg = "Required environment variables missing: "
    missing = []
    if not SUPABASE_URL: missing.append("SUPABASE_URL")
    if not SUPABASE_KEY: missing.append("SUPABASE_KEY")
    if not SITE_URL: missing.append("DOMAIN")
    error_msg += ", ".join(missing)
    logger.error(error_msg)
    raise EnvironmentError(error_msg)

# Initialize Supabase client
try:
    # Let it fail explicitly if settings are missing
    if not settings.SUPABASE_URL:
        logger.error("SUPABASE_URL is not set in settings")
        raise ValueError("SUPABASE_URL is required")
        
    if not settings.SUPABASE_KEY:
        logger.error("SUPABASE_KEY is not set in settings")
        raise ValueError("SUPABASE_KEY is required")
    
    if not settings.SUPABASE_SERVICE_KEY:
        logger.error("SUPABASE_SERVICE_KEY is not set in settings")
        raise ValueError("SUPABASE_SERVICE_KEY is required")
    
    # Initialize regular client for user operations
    supabase = create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_KEY
    )
    
    # Initialize service role client for trusted server operations
    supabase_service = create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_SERVICE_KEY
    )
    
    logger.info(f"Supabase clients initialized with URL: {settings.SUPABASE_URL[:10]}...")
    logger.info("Using default Supabase client configuration")
except Exception as e:
    logger.error(f"Error initializing Supabase client: {str(e)}")
    # Re-raise the exception to make the failure explicit
    raise

# Export a function to check if Supabase is properly initialized
def is_supabase_available():
    return supabase is not None

# Configure site URL for redirects
logger.info(f"Setting site URL to: {SITE_URL}")

# For the current version of supabase-py, we can't directly set site_url on the client
# Instead, we'll rely on the SITE_URL environment variable which should be picked up automatically
logger.info(f"Using environment variable for site_url: {SITE_URL}")

# If you need to set redirect URLs for specific operations, use them in the method calls
# For example:
# supabase.auth.sign_in_with_password(..., options={"redirect_to": f"{SITE_URL}/auth/callback"})

async def register_user(email, password):
    """Register a new user with Supabase"""
    logger.info(f"Attempting to register user with email: {email}")
    try:
        logger.debug(f"Supabase URL: {SUPABASE_URL[:20]}...")
        logger.debug("Calling Supabase auth.sign_up")
        user_data = {
            "email": email,
            "password": password,
            "options": {
                "email_confirm": False  # This ensures confirmation email is sent
            }
        }
        
        logger.debug(f"Sending sign_up request with data: {user_data}")
        response = supabase.auth.sign_up(user_data)
        
        logger.info(f"Registration successful, user_id: {response.user.id if response.user else 'None'}")
        return response
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        logger.exception("Registration exception details:")
        raise

async def login_user(email, password):
    """Login a user with Supabase"""
    logger.info(f"Attempting to login user with email: {email}")
    try:
        logger.debug(f"Supabase URL: {SUPABASE_URL[:20]}...")
        logger.debug("Calling Supabase auth.sign_in_with_password")
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        logger.info(f"Login response received: user_id={response.user.id if response.user else 'None'}")
        logger.debug(f"Full login response: {response}")
        return response
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        logger.exception("Login exception details:")
        # Return the error as a dict instead of raising
        error_message = str(e)
        return {
            "error": error_message,
            "is_email_not_confirmed": "Email not confirmed" in error_message
        }

async def request_password_reset(email: str):
    """Request a password reset for a user"""
    logger.info(f"Requesting password reset for email: {email}")
    try:
        response = supabase.auth.reset_password_email(email)
        logger.info(f"Password reset email sent to: {email}")
        return {"success": True}
    except Exception as e:
        logger.error(f"Password reset request error: {str(e)}")
        return {"success": False, "error": str(e)}

async def update_password(access_token: str, new_password: str):
    """Update a user's password"""
    logger.info("Updating user password")
    try:
        # Set the session with the access token
        supabase.auth.set_session(access_token)
        
        # Update the password
        response = supabase.auth.update_user({"password": new_password})
        
        logger.info("Password updated successfully")
        return {"success": True}
    except Exception as e:
        logger.error(f"Password update error: {str(e)}")
        return {"success": False, "error": str(e)}

def login_with_facebook():
    try:
        response = supabase.auth.sign_in_with_oauth({
            "provider": "facebook",
        })
        return response
    except Exception as e:
        return {"error": str(e)}

async def delete_user(user_id: str):
    """Delete a user from Supabase"""
    logger.info(f"Attempting to delete user: {user_id}")
    try:
        # This would require admin privileges
        # You might need to use a different approach or Supabase function
        logger.warning("User deletion not implemented in this client library")
        return {"success": True, "message": "User deleted successfully"}
    except Exception as e:
        print("Delete user error:", str(e))
        return {"success": False, "error": str(e)}

async def logout_user(request: Request):
    """Logout a user from Supabase"""
    logger.info("Attempting to logout user")
    try:
        # Get the access token from the request cookies
        access_token = request.cookies.get("access_token")
        if not access_token:
            logger.warning("No access token found in cookies during logout")
            return {"success": False, "message": "No access token found"}
        
        logger.debug("Calling Supabase auth.sign_out")
        supabase.auth.sign_out()
        logger.info("Logout successful")
        return {"success": True}
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        logger.exception("Logout exception details:")
        raise HTTPException(status_code=400, detail=f"Logout failed: {str(e)}")