from fastapi import Request, HTTPException, Depends
from fastapi.responses import RedirectResponse, JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.auth.supabase_auth import supabase
import jwt
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define public routes that don't require authentication
PUBLIC_ROUTES = [
    "/",
    "/auth/login",
    "/auth/register",
    "/auth/reset-password",
    "/auth/callback",
    "/auth/session",
    "/auth/resend-confirmation",
    "/legal/privacy-policy",
    "/legal/terms-of-service",
    "/static",
    "/favicon.ico",
    "/sitemap",
    "/routes",
]

# Define prefixes for routes that don't require authentication
PUBLIC_PREFIXES = [
    "/static/",
    "/auth/",
    "/legal/",
    "/api/public/",
    "/webhooks/",
]

# Make sure /connections is NOT in these lists

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        logger.info(f"Auth middleware processing request to: {request.url.path}")
        
        # Skip auth for public routes
        if request.url.path in PUBLIC_ROUTES or any(request.url.path.startswith(prefix) for prefix in PUBLIC_PREFIXES):
            logger.info(f"Skipping auth for public route: {request.url.path}")
            return await call_next(request)
        
        # Check if the path starts with /connections/ but is not exactly /connections
        if request.url.path.startswith("/connections/") and request.url.path != "/connections":
            # For OAuth callbacks and other connection-related routes
            return await call_next(request)
        
        # Get token from cookies
        access_token = request.cookies.get("access_token")

        if not access_token:
            logger.warning(f"No token found for protected route: {request.url.path}")
            return RedirectResponse(url="/auth/login", status_code=303)

        try:
            logger.debug(f"Verifying token: {access_token[:10]}...")
            # Verify the token with Supabase
            user = supabase.auth.get_user(access_token)
            
            logger.debug(f"Token verification result: {user}")
            if not user or not user.user:
                logger.warning(f"Invalid token for protected route: {request.url.path}")
                return RedirectResponse(url="/auth/login", status_code=303)
            
            # Add user to request state
            request.state.user = user.user
            logger.info(f"User authenticated: {user.user.id}")
            
            return await call_next(request)
        except Exception as e:
            logger.error(f"Auth error: {str(e)}")
            
            # Check if token is expired
            if "token is expired" in str(e).lower():
                # Try to refresh the token
                refresh_token = request.cookies.get("refresh_token")
                if refresh_token:
                    try:
                        logger.info("Attempting to refresh token")
                        response = supabase.auth.refresh_session(refresh_token)
                        
                        if response and response.session:
                            # Create a new response with the refreshed token
                            original_response = await call_next(request)
                            
                            # Set the new tokens in cookies
                            original_response.set_cookie(
                                key="access_token",
                                value=response.session.access_token,
                                httponly=True,
                                max_age=3600,
                                secure=getattr(settings, 'cookie_secure', False),
                                samesite=getattr(settings, 'cookie_samesite', 'lax')
                            )
                            original_response.set_cookie(
                                key="refresh_token",
                                value=response.session.refresh_token,
                                httponly=True,
                                max_age=7 * 24 * 3600,
                                secure=getattr(settings, 'cookie_secure', False),
                                samesite=getattr(settings, 'cookie_samesite', 'lax')
                            )
                            
                            return original_response
                    except Exception as refresh_error:
                        logger.error(f"Token refresh error: {str(refresh_error)}")
            
            # If we get here, authentication failed
            return RedirectResponse(url="/auth/login", status_code=303)

async def get_current_user_id(request: Request):
    """Get the current user ID from the request state"""
    user_id = getattr(request.state, "user_id", None)
    
    # Log for debugging
    logger.debug(f"get_current_user_id called, user_id from state: {user_id}")
    
    if not user_id:
        # Try to get user_id from token in cookie
        token = request.cookies.get("session_token")
        if token:
            try:
                payload = jwt.decode(token, options={"verify_signature": False})
                user_id = payload.get("sub")
                logger.debug(f"Extracted user_id from token: {user_id}")
            except Exception as e:
                logger.error(f"Error decoding token: {str(e)}")
        
        if not user_id:
            logger.warning("No user_id found in request state or token")
            raise HTTPException(
                status_code=401,
                detail="Not authenticated"
            )
    
    return user_id