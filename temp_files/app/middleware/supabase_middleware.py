from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.auth.supabase_auth import supabase
import logging
import os
from app.config import settings
from fastapi.templating import Jinja2Templates
import jwt

logger = logging.getLogger(__name__)
templates = Jinja2Templates(directory="templates")

class SupabaseConnectionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            # Get access token from cookies
            access_token = request.cookies.get("access_token")
            
            if access_token:
                try:
                    # Set the session on the Supabase client
                    supabase.auth.set_session(access_token, "")  # Empty string for refresh_token
                    logger.info("Successfully set Supabase session from access token")
                    
                    # Try to decode the token to get user info (without verification)
                    try:
                        payload = jwt.decode(access_token, options={"verify_signature": False})
                        request.state.user_id = payload.get("sub")
                        logger.debug(f"Extracted user_id from token: {request.state.user_id}")
                    except Exception as e:
                        logger.error(f"Error decoding JWT token: {str(e)}")
                except Exception as e:
                    logger.error(f"Error setting Supabase session: {str(e)}")
            
            response = await call_next(request)
            return response
            
        except Exception as e:
            error_message = str(e)
            logger.error(f"Supabase middleware error: {error_message}")
            
            # Check if the request accepts HTML
            accept_header = request.headers.get("accept", "")
            if "text/html" in accept_header:
                # Return HTML error page
                return templates.TemplateResponse(
                    "error.html",
                    {
                        "request": request,
                        "status_code": 500,
                        "detail": "Supabase connection error",
                        "settings": {
                            **settings.dict(),
                            "SUPABASE_URL": os.getenv("SUPABASE_URL"),
                            "SUPABASE_ANON_KEY": os.getenv("SUPABASE_KEY")
                        }
                    },
                    status_code=500
                )
            else:
                # Return JSON error for API requests
                return JSONResponse(
                    status_code=500,
                    content={"error": "Database connection error", "details": str(e)}
                ) 