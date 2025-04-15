from pydantic_settings import BaseSettings
from functools import lru_cache
import os
import logging
from pydantic import validator

class Settings(BaseSettings):
    """Application settings"""
    # Environment settings
    ENV: str = os.getenv("APP_ENV", "development")
    DEBUG: bool = True
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    
    # URL configuration
    DOMAIN: str = os.getenv("DOMAIN", "http://localhost:8000")
    
    # For backward compatibility
    @property
    def domain(self):
        return self.DOMAIN
    
    @property
    def base_url(self):
        return self.DOMAIN
    
    # API key settings
    API_KEY_HEADER: str = "X-API-Key"
    
    # Supabase settings
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
    SUPABASE_SERVICE_KEY: str = os.getenv("SUPABASE_SERVICE_KEY", "")
    
    app_name: str = "Pablo"
    notion_client_id: str = os.getenv("NOTION_CLIENT_ID", "")
    notion_client_secret: str = os.getenv("NOTION_CLIENT_SECRET", "")
    facebook_client_id: str = os.getenv("FACEBOOK_CLIENT_ID", "")
    facebook_client_secret: str = os.getenv("FACEBOOK_CLIENT_SECRET", "")
    facebook_api_version: str = "v21.0"
    airtable_client_id: str = os.getenv("AIRTABLE_CLIENT_ID", "")
    airtable_client_secret: str = os.getenv("AIRTABLE_CLIENT_SECRET", "")

    # OAuth redirect URIs
    @property
    def notion_redirect_uri(self) -> str:
        return f"{self.DOMAIN}/connections/notion/callback"
    
    @property
    def facebook_redirect_uri(self) -> str:
        return f"{self.DOMAIN}/connections/facebook/callback"

    # Add validation for Supabase credentials
    @validator('SUPABASE_URL')
    def validate_supabase_url(cls, v):
        if not v:
            logging.warning("SUPABASE_URL is not set!")
        return v
    
    @validator('SUPABASE_KEY')
    def validate_supabase_key(cls, v):
        if not v:
            logging.warning("SUPABASE_KEY is not set!")
        elif len(v) < 10:
            logging.warning("SUPABASE_KEY appears to be too short!")
        return v

    # Add cookie settings
    cookie_secure: bool = False  # Set to True in production
    cookie_samesite: str = "lax"  # Options: strict, lax, none

    @property
    def app_url(self) -> str:
        return self.DOMAIN

    @property
    def airtable_redirect_uri(self) -> str:
        base_url = self.app_url.rstrip('/')
        return f"{base_url}/connections/airtable/callback"

    # Base URL for the application
    base_url: str = os.getenv("DOMAIN", "https://pablo.social")
    
    # Cloudflare Turnstile settings
    cloudflare_turnstile_site_key: str = os.getenv("CLOUDFLARE_TURNSTILE_SITE_KEY")
    cloudflare_turnstile_secret_key: str = os.getenv("CLOUDFLARE_TURNSTILE_SECRET_KEY")

    class Config:
        env_file = ".env"
        extra = "ignore" 

@lru_cache()
def get_settings():
    return Settings()

# Add this line to export a pre-initialized settings object
settings = get_settings() 