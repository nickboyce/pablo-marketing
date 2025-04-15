import os
from fastapi import HTTPException
from httpx import AsyncClient
from app.auth.supabase_auth import supabase
from datetime import datetime, timedelta
from app.config import get_settings
import logging

settings = get_settings()
logger = logging.getLogger(__name__)

class FacebookOAuth:
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        self.app_id = client_id
        self.app_secret = client_secret
        self.api_version = settings.facebook_api_version
        self.redirect_uri = redirect_uri
        self.auth_url = f"https://www.facebook.com/{self.api_version}/dialog/oauth"
        self.token_url = f"https://graph.facebook.com/{self.api_version}/oauth/access_token"
    
    def get_auth_url(self, state: str) -> str:
        """
        Generate the Facebook OAuth authorization URL with all required permissions.
        """
        # Define all permissions needed
        permissions = [
            "public_profile",
            "email",
            "ads_read",
            "ads_management",
            "business_management",
            "pages_show_list",
            "pages_read_engagement",
            "pages_manage_ads",
            "pages_manage_posts"
        ]
        
        # Join permissions with commas
        scope = ",".join(permissions)
        
        # Build the authorization URL
        auth_url = (
            f"https://www.facebook.com/{self.api_version}/dialog/oauth"
            f"?client_id={self.app_id}"
            f"&redirect_uri={self.redirect_uri}"
            f"&state={state}"
            f"&scope={scope}"
        )
        
        return auth_url
    
    async def get_access_token(self, code: str) -> dict:
        """Get initial short-lived token and exchange for long-lived token"""
        async with AsyncClient() as client:
            # Get initial short-lived token
            response = await client.get(
                self.token_url,
                params={
                    "client_id": self.app_id,
                    "client_secret": self.app_secret,
                    "redirect_uri": self.redirect_uri,
                    "code": code
                }
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=400, detail="Failed to get access token")
            
            token_data = response.json()
            
            # Exchange for long-lived token
            exchange_url = f"https://graph.facebook.com/{self.api_version}/oauth/access_token"
            exchange_params = {
                "grant_type": "fb_exchange_token",
                "client_id": self.app_id,
                "client_secret": self.app_secret,
                "fb_exchange_token": token_data["access_token"]
            }
            
            exchange_response = await client.get(exchange_url, params=exchange_params)
            if exchange_response.status_code != 200:
                raise HTTPException(status_code=400, detail="Failed to exchange for long-lived token")
            
            long_lived_data = exchange_response.json()
            
            # Combine the data, preferring long-lived token data
            return {
                "access_token": long_lived_data["access_token"],
                "expires_in": long_lived_data.get("expires_in", 5184000),  # Default to 60 days if not provided
                "token_type": "bearer"
            }
    
    async def store_token(self, user_id: str, token_data: dict) -> None:
        """Store Facebook tokens in Supabase"""
        try:
            # Calculate expiry time
            now = datetime.now()
            access_token_expires = now + timedelta(seconds=token_data["expires_in"])
            logger.info(f"Token will expire at: {access_token_expires.isoformat()}")
            
            # Prepare data for storage
            data = {
                "user_id": user_id,
                "service_name": "facebook",
                "access_token": token_data["access_token"],
                "access_token_expires": access_token_expires.isoformat(),
                "updated_at": now.isoformat(),
                "metadata": {}  # Empty JSON object, not a string
            }
            
            # Log the exact data being sent
            logger.info(f"Attempting to store data in Supabase: {data}")
            
            # Check if credentials already exist
            existing = supabase.table('service_credentials').select('*').eq('user_id', user_id).eq('service_name', 'facebook').execute()
            
            if existing.data:
                logger.info(f"Updating existing Facebook credentials for user {user_id}")
                # Update existing credentials
                response = supabase.table('service_credentials').update(data).eq('user_id', user_id).eq('service_name', 'facebook').execute()
                logger.info(f"Update response: {response}")
            else:
                logger.info(f"Storing new Facebook credentials for user {user_id}")
                # Insert new credentials
                response = supabase.table('service_credentials').insert(data).execute()
                logger.info(f"Insert response: {response}")
            
            if not response.data:
                raise Exception("No data returned from Supabase operation")
            
            logger.info(f"Successfully stored Facebook token for user {user_id}")
                
        except Exception as e:
            logger.error(f"Error storing Facebook tokens: {str(e)}")
            raise

facebook_oauth = FacebookOAuth(
    client_id=settings.facebook_client_id,
    client_secret=settings.facebook_client_secret,
    redirect_uri=settings.facebook_redirect_uri
) 
