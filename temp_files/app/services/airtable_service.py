import logging
from httpx import AsyncClient
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class AirtableService:
    def __init__(self, credentials: Dict[str, Any]):
        """Initialize Airtable service with user's credentials"""
        # Ensure credentials is the specific dict for Airtable
        logger.info(f"Initializing AirtableService with credentials: {credentials.keys()}")
        self.credentials = credentials
        self.base_url = "https://api.airtable.com/v0"
        
    def _get_token(self) -> str:
        """Get Airtable token from credentials"""
        try:
            # Directly use self.credentials, which is already the Airtable specific dict
            if not self.credentials:
                raise Exception("Airtable credentials dictionary is empty")
                
            # Get the access token directly from self.credentials
            access_token = self.credentials.get('access_token')
            if not access_token:
                raise Exception("No Airtable access token found in provided credentials")
                
            logger.info("Successfully retrieved Airtable access token")
            return access_token
            
        except Exception as e:
            logger.error(f"Failed to get Airtable token: {str(e)}")
            raise Exception("Failed to get Airtable token")
    
    async def get_record(self, base_id: str, table_id: str, record_id: str) -> Dict[str, Any]:
        """Fetch a single record from Airtable"""
        logger.info(f"Attempting to fetch Airtable record: base={base_id}, table={table_id}, record={record_id}")
        # Get the token
        token = self._get_token()
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        async with AsyncClient() as client:
            url = f"{self.base_url}/{base_id}/{table_id}/{record_id}"
            logger.info(f"Requesting URL: {url}")
            response = await client.get(url, headers=headers)
            
            logger.info(f"Airtable API response status: {response.status_code}")
            if response.status_code != 200:
                logger.error(f"Failed to get record (status {response.status_code}): {response.text}")
                raise Exception(f"Failed to get record: {response.text}")
            
            logger.info("Successfully fetched record from Airtable API")
            return response.json() 