from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.services.connection_service import ConnectionService
from app.auth.supabase_auth import supabase
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)
connection_service = ConnectionService(supabase)

class TokenRefreshMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Only check on certain routes that use Facebook API
        if "/facebook/" in request.url.path or "/ads/" in request.url.path:
            try:
                # Get user ID from state instead of session
                user_id = getattr(request.state, "user_id", None)
                
                # Try to get from token if not in state
                if not user_id:
                    import jwt
                    token = request.cookies.get("session_token")
                    if token:
                        try:
                            payload = jwt.decode(token, options={"verify_signature": False})
                            user_id = payload.get("sub")
                        except Exception as e:
                            logger.error(f"Error decoding token: {str(e)}")
                
                if user_id:
                    # Check if Facebook token needs refresh
                    await self.check_and_refresh_facebook_token(user_id)
            except Exception as e:
                logger.error(f"Error in token refresh middleware: {str(e)}")
        
        response = await call_next(request)
        return response
    
    async def check_and_refresh_facebook_token(self, user_id):
        """Check if Facebook token needs refresh and refresh if needed"""
        try:
            # Get Facebook credentials
            response = supabase.table('service_credentials')\
                .select("*")\
                .eq('user_id', user_id)\
                .eq('service_name', 'facebook')\
                .execute()
            
            if not response.data:
                return
            
            credentials = response.data[0]
            
            # Check if token is expired or about to expire (within 1 day)
            if "expires_at" in credentials:
                expires_at = datetime.fromisoformat(credentials["expires_at"])
                
                if expires_at - timedelta(days=1) <= datetime.now():
                    # Token is about to expire, refresh it
                    from app.routers.connections import exchange_for_long_lived_token
                    from app.config import get_settings
                    
                    settings = get_settings()
                    
                    # Exchange for a new long-lived token
                    new_token = await exchange_for_long_lived_token(
                        credentials["access_token"],
                        settings.facebook_client_id,
                        settings.facebook_client_secret
                    )
                    
                    # Update the token in the database
                    await connection_service.save_credentials(
                        user_id=user_id,
                        service_name="facebook",
                        access_token=new_token,
                        provider_user_id=credentials.get("provider_user_id"),
                        metadata={
                            **credentials.get("metadata", {}),
                            "token_type": "refreshed_long_lived",
                            "refreshed_at": datetime.now().isoformat()
                        }
                    )
                    
                    logger.info(f"Refreshed Facebook token for user {user_id}")
        
        except Exception as e:
            logger.error(f"Error checking/refreshing Facebook token: {str(e)}") 