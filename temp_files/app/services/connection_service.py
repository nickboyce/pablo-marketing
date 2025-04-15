from typing import List, Optional
from pydantic import BaseModel
from supabase import Client
from datetime import datetime
import logging
from app.auth.supabase_auth import supabase, supabase_service
from app.services.airtable_service import AirtableService

logger = logging.getLogger(__name__)

class Connection(BaseModel):
    service_name: str
    access_token: str
    refresh_token: Optional[str] = None
    updated_at: datetime

class ConnectionService:
    def __init__(self, supabase_client: Client = None):
        self.supabase = supabase_client or supabase_service

    async def store_connection(self, user_id: str, connection: Connection) -> Connection:
        data = {
            "user_id": user_id,
            **connection.dict()
        }
        
        existing = self.supabase.table('service_credentials')\
            .select("*")\
            .eq('user_id', user_id)\
            .eq('service_name', connection.service_name)\
            .execute()

        if existing.data:
            response = self.supabase.table('service_credentials')\
                .update(data)\
                .eq('user_id', user_id)\
                .eq('service_name', connection.service_name)\
                .execute()
        else:
            response = self.supabase.table('service_credentials')\
                .insert(data)\
                .execute()
        
        return Connection(**response.data[0])

    def get_user_connections(self, user_id):
        """Get all connections for a user"""
        try:
            # Get service credentials
            response = self.supabase.table('service_credentials')\
                .select("*")\
                .eq('user_id', user_id)\
                .execute()
            
            logger.info(f"Retrieved {len(response.data)} service credentials for user {user_id}")
            
            # Organize credentials by service, filtering out null tokens
            credentials = {}
            for cred in response.data:
                service_name = cred.get('service_name')
                access_token = cred.get('access_token')
                
                # Only include credentials that have a non-null access token
                if access_token is not None and access_token != "":
                    logger.info(f"Including connected service: {service_name}")
                    credentials[service_name] = cred
                else:
                    logger.info(f"Skipping disconnected service: {service_name}")
            
            # Get API key
            api_key_response = self.supabase.table('api_keys')\
                .select("key")\
                .eq('user_id', user_id)\
                .execute()
            
            api_key = None
            if api_key_response.data:
                api_key = api_key_response.data[0]['key']
                logger.info(f"Found API key for user {user_id}")
            else:
                logger.info(f"No API key found for user {user_id}")
            
            result = {
                'credentials': credentials,
                'api_key': api_key
            }
            logger.info(f"Connected services: {list(credentials.keys())}")
            return result
            
        except Exception as e:
            logger.error(f"Error getting user connections: {str(e)}")
            return {'credentials': {}, 'api_key': None}

    async def get_airtable_service(self, user_id: str) -> Optional[AirtableService]:
        """Get an initialized AirtableService for a user"""
        try:
            # Get user's connections
            connections = self.get_user_connections(user_id)
            if not connections or 'credentials' not in connections:
                logger.error(f"No connections found for user {user_id}")
                return None

            airtable_credentials = connections['credentials'].get('airtable')
            if not airtable_credentials or not airtable_credentials.get('access_token'):
                logger.error(f"No Airtable credentials found for user {user_id}")
                return None

            logger.info(f"Found Airtable credentials for user {user_id}")
            return AirtableService(credentials=airtable_credentials)

        except Exception as e:
            logger.error(f"Error getting Airtable service: {str(e)}")
            return None

# Create a singleton instance
connection_service = ConnectionService() 