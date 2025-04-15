from typing import Dict, Any, Optional, Union, Tuple
import secrets
import string
from datetime import datetime
import logging
from supabase import Client
from app.auth.supabase_auth import supabase
from app.config import get_settings
from supabase import create_client
import os

logger = logging.getLogger(__name__)
settings = get_settings()

# Create a separate admin client for API key operations
try:
    # Require both URL and service key
    if not settings.SUPABASE_URL:
        raise ValueError("SUPABASE_URL is required for API key operations")
    if not settings.SUPABASE_SERVICE_KEY:
        raise ValueError("SUPABASE_SERVICE_KEY is required for API key operations")
    
    # Initialize admin client with service role key
    supabase_admin = create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_SERVICE_KEY
    )
    logger.info("Initialized Supabase admin client for API key operations")
except Exception as e:
    logger.error(f"Failed to initialize Supabase admin client: {str(e)}")
    raise

class ApiKeyService:
    def __init__(self, supabase_client=None):
        # Only use the admin client - no fallbacks
        if not supabase_admin:
            raise RuntimeError("Supabase admin client not initialized")
        self.client = supabase_admin
        self.logger = logging.getLogger(__name__)
    
    async def generate_key(self, user_id: str):
        """Generate a new API key for a user"""
        try:
            # Generate a random API key
            key = self._generate_random_key()
            
            # Insert the key into the database using admin client
            response = self.client.table('api_keys').insert({
                "user_id": user_id,
                "key": key,
                "created_at": datetime.now().isoformat()
            }).execute()
            
            self.logger.info(f"Generated API key for user {user_id}")
            return response.data[0] if response.data else None
        except Exception as e:
            self.logger.error(f"Error generating API key: {str(e)}")
            raise
    
    async def list_keys(self, user_id: str):
        """List all API keys for a user"""
        try:
            response = self.client.table('api_keys').select("*").eq('user_id', user_id).execute()
            return response.data
        except Exception as e:
            self.logger.error(f"Error listing API keys: {str(e)}")
            raise
    
    async def delete_key(self, key_id: str):
        """Delete an API key"""
        try:
            response = self.client.table('api_keys').delete().eq('id', key_id).execute()
            return True
        except Exception as e:
            self.logger.error(f"Error deleting API key: {str(e)}")
            raise
    
    def _generate_random_key(self, length=32):
        """Generate a random API key string"""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    async def validate_api_key(self, api_key: str) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
        """
        Validate an API key and return the associated user_id and response object
        
        Args:
            api_key: The API key to validate
            
        Returns:
            tuple: (user_id, response_object)
                - user_id: The user_id associated with the key if valid, None otherwise
                - response_object: A dict with error details if validation failed, None if successful
        """
        try:
            self.logger.info(f"Validating API key: {api_key[:8]}...")
            
            response = self.client.table('api_keys')\
                .select("user_id")\
                .eq('key', api_key)\
                .execute()
            
            if not response.data:
                self.logger.error(f"No matching API key found in database")
                return None, {
                    "status_code": 401,
                    "content": {"error": "Invalid API key"}
                }
            
            user_id = response.data[0]['user_id']
            self.logger.info(f"API key validated successfully for user_id: {user_id}")
            
            # Update last_used_at
            self.client.table('api_keys')\
                .update({"last_used_at": datetime.now().isoformat()})\
                .eq('key', api_key)\
                .execute()
            
            return user_id, None
            
        except Exception as e:
            self.logger.error(f"Error validating API key: {str(e)}")
            return None, {
                "status_code": 500,
                "content": {"error": f"Error validating API key: {str(e)}"}
            }

# Create a singleton instance
api_key_service = ApiKeyService()

async def generate_api_key_for_user(user_id: str):
    """Generate an API key for a user"""
    return await api_key_service.generate_key(user_id) 