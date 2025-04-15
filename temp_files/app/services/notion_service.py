import logging
from notion_client import Client
from app.auth.supabase_auth import supabase, supabase_service
from datetime import datetime
import json
from dotenv import load_dotenv
from app.models import NotionPayload, AdData

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def pretty_json(obj):
    """Format object as pretty JSON string"""
    return json.dumps(obj, indent=2, sort_keys=True, default=str)

class NotionService:
    def __init__(self, token, user_id=None):
        self.client = Client(auth=token)
        self.user_id = user_id
    
    async def get_page(self, page_id: str) -> dict:
        """Fetch a page from Notion"""
        try:
            page = self.client.pages.retrieve(page_id=page_id)
            logger.info(f"Retrieved Notion page: {pretty_json(page)}")
            return page
        except Exception as e:
            logger.error(f"Error fetching Notion page: {str(e)}")
            raise
    
    async def update_page_status(self, page_id: str, status: str) -> dict:
        """Update a page's status in Notion"""
        try:
            # Map our status to Notion's status options
            status_mapping = {
                "building": "In Progress",
                "complete": "Complete",
                "error": "Error"
            }
            notion_status = status_mapping.get(status, "Draft")
            
            # Update the page
            response = self.client.pages.update(
                page_id=page_id,
                properties={
                    "ad_import_status": {
                        "status": {
                            "name": notion_status
                        }
                    }
                }
            )
            logger.info(f"Updated Notion page status: {pretty_json(response)}")
            return response
        except Exception as e:
            logger.error(f"Error updating Notion page status: {str(e)}")
            raise
    
    async def process_page(self, page_id: str) -> dict:
        """Process a Notion page and update its status"""
        try:
            # Get the page data
            page_data = await self.get_page(page_id)
            
            # Create NotionPayload from page data
            notion_payload = NotionPayload(data=page_data)
            
            # Transform to generic AdData
            ad_data = notion_payload.to_ad_data(self.user_id)
            
            # Save to Supabase
            data = ad_data.dict()
            data["ad_import_status"] = "building"
            
            # Log the data we're sending to Supabase
            logger.info(f"Sending data to Supabase: {pretty_json(data)}")
            
            response = supabase_service.table('ad_imports').insert(data).execute()
            
            if not response.data:
                raise Exception("No data returned from Supabase insert")
            
            # Update Notion page status
            await self.update_page_status(page_id, "building")
            
            return {
                "status": "success",
                "message": "Page processed successfully",
                "ad_name": data["ad_name"]
            }
            
        except Exception as e:
            logger.error(f"Error processing Notion page: {str(e)}")
            # Update Notion page status to error
            try:
                await self.update_page_status(page_id, "error")
            except:
                pass
            raise 