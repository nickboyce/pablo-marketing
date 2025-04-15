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

class AirtableOAuth:
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        # Strip any whitespace that might have been accidentally included
        self.client_id = client_id.strip() if client_id else ""
        self.client_secret = client_secret.strip() if client_secret else ""
        self.redirect_uri = redirect_uri
        self.auth_url = "https://airtable.com/oauth2/v1/authorize"
        self.token_url = "https://airtable.com/oauth2/v1/token"
        self.code_verifier = None
        self.scope = "data.records:read data.records:write schema.bases:read webhook:manage"
    
    def generate_code_verifier(self) -> str:
        """Generate a code verifier for PKCE"""
        import secrets
        code_verifier = secrets.token_urlsafe(64)
        # Trim to a valid length (between 43-128 characters)
        if len(code_verifier) > 128:
            code_verifier = code_verifier[:128]
        elif len(code_verifier) < 43:
            code_verifier = code_verifier + 'A' * (43 - len(code_verifier))
        
        self.code_verifier = code_verifier
        return code_verifier

    def generate_code_challenge(self, code_verifier: str) -> str:
        """Generate a code challenge from the code verifier using S256 method"""
        code_challenge = hashlib.sha256(code_verifier.encode('utf-8')).digest()
        code_challenge = base64.urlsafe_b64encode(code_challenge).decode('utf-8')
        # Remove padding characters
        code_challenge = code_challenge.replace('=', '')
        return code_challenge
    
    def get_auth_url(self, state: str) -> str:
        """Generate the Airtable OAuth authorization URL"""
        # Define the scopes needed
        scopes = [
            "data.records:read",
            "data.records:write",
            "schema.bases:read"
        ]
        
        # Join scopes with spaces for Airtable
        scope = " ".join(scopes)
        
        # Generate PKCE code verifier and challenge
        code_verifier = self.generate_code_verifier()
        code_challenge = self.generate_code_challenge(code_verifier)
        
        # Use the most basic approach possible
        auth_url = (
            f"{self.auth_url}"
            f"?client_id={self.client_id}"
            f"&redirect_uri={urllib.parse.quote(self.redirect_uri)}"
            f"&response_type=code"
            f"&state={state}"
            f"&scope={scope}"
            f"&code_challenge={code_challenge}"
            f"&code_challenge_method=S256"
        )
        
        logger.info(f"Generated Airtable auth URL: {auth_url}")
        logger.info(f"Code verifier (first 10 chars): {code_verifier[:10]}...")
        return auth_url

    async def get_access_token(self, code: str) -> dict:
        """Exchange authorization code for access token"""
        if not self.code_verifier:
            raise HTTPException(status_code=400, detail="Code verifier not found. Please restart the OAuth flow.")
        
        async with AsyncClient() as client:
            response = await client.post(
                self.token_url,
                auth=(self.client_id, self.client_secret),
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": self.redirect_uri,
                    "code_verifier": self.code_verifier
                }
            )
            
            if response.status_code != 200:
                logger.error(f"Token exchange failed with status {response.status_code}: {response.text}")
                raise HTTPException(status_code=400, detail=f"Failed to get access token: {response.text}")
            
            token_data = response.json()
            logger.info("Successfully obtained Airtable access token")
            return token_data

    async def store_token(self, user_id: str, token_data: dict) -> None:
        """Store Airtable tokens in Supabase"""
        try:
            # Calculate expiry time for access token
            now = datetime.now()
            access_token_expires = now + timedelta(seconds=token_data["expires_in"])
            
            # Prepare data for storage
            data = {
                "user_id": user_id,
                "service_name": "airtable",
                "access_token": token_data["access_token"],
                "refresh_token": token_data["refresh_token"],
                "access_token_expires": access_token_expires.isoformat()
            }
            
            # Check if credentials already exist
            existing = supabase.table('service_credentials').select('*').eq('user_id', user_id).eq('service_name', 'airtable').execute()
            
            if existing.data:
                # Update existing credentials
                response = supabase.table('service_credentials').update(data).eq('user_id', user_id).eq('service_name', 'airtable').execute()
                logger.info("Updated existing Airtable credentials")
            else:
                # Insert new credentials
                response = supabase.table('service_credentials').insert(data).execute()
                logger.info("Stored new Airtable credentials")
            
            if not response.data:
                raise Exception("No data returned from Supabase operation")
                
        except Exception as e:
            logger.error(f"Error storing Airtable tokens: {str(e)}")
            raise

# Initialize the OAuth handler with settings
airtable_oauth = AirtableOAuth(
    client_id=settings.airtable_client_id,
    client_secret=settings.airtable_client_secret,
    redirect_uri=settings.airtable_redirect_uri
)

# Add startup logging
logger.info(f"Airtable OAuth initialized with:")
logger.info(f"  - Client ID exists: {bool(airtable_oauth.client_id)}")
logger.info(f"  - Client Secret exists: {bool(airtable_oauth.client_secret)}")
logger.info(f"  - Redirect URI: {airtable_oauth.redirect_uri}") 