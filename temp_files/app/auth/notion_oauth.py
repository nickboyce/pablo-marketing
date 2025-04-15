import os
from fastapi import HTTPException
from httpx import AsyncClient
from app.auth.supabase_auth import supabase
from datetime import datetime, timedelta
from app.config import get_settings
from urllib.parse import quote
import logging
import urllib.parse
import hashlib
import base64

settings = get_settings()
logger = logging.getLogger(__name__)

class NotionOAuth:
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.auth_url = "https://api.notion.com/v1/oauth/authorize"
        self.token_url = "https://api.notion.com/v1/oauth/token"
    
    def get_auth_url(self, state: str) -> str:
        return f"{self.auth_url}?client_id={self.client_id}&redirect_uri={self.redirect_uri}&response_type=code&state={state}&owner=user"

    async def get_access_token(self, code: str) -> dict:
        async with AsyncClient() as client:
            response = await client.post(
                self.token_url,
                auth=(self.client_id, self.client_secret),
                json={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": self.redirect_uri
                }
            )
            if response.status_code != 200:
                raise HTTPException(status_code=400, detail="Failed to get access token")
            
            token_data = response.json()
            logger.info(f"Notion token response: {token_data}")
            return token_data

    async def store_token(self, user_id: str, token_data: dict) -> None:
        """Store Notion tokens in Supabase"""
        try:
            # Calculate expiry time for access token
            now = datetime.now()
            access_token_expires = now + timedelta(days=365)  # 1 year
            
            # Prepare data for storage
            data = {
                "user_id": user_id,
                "service_name": "notion",
                "access_token": token_data["access_token"],
                "refresh_token": None,  # Notion doesn't use refresh tokens
                "access_token_expires": access_token_expires.isoformat()
            }
            
            # Check if credentials already exist
            existing = supabase.table('service_credentials').select('*').eq('user_id', user_id).eq('service_name', 'notion').execute()
            
            if existing.data:
                # Update existing credentials
                response = supabase.table('service_credentials').update(data).eq('user_id', user_id).eq('service_name', 'notion').execute()
                logger.info("Updated existing Notion credentials")
            else:
                # Insert new credentials
                response = supabase.table('service_credentials').insert(data).execute()
                logger.info("Stored new Notion credentials")
            
            if not response.data:
                raise Exception("No data returned from Supabase operation")
                
        except Exception as e:
            logger.error(f"Error storing Notion tokens: {str(e)}")
            raise

notion_oauth = NotionOAuth(
    client_id=settings.notion_client_id,
    client_secret=settings.notion_client_secret,
    redirect_uri=settings.notion_redirect_uri
) 