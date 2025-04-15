from typing import Dict, Any, Optional
import logging
from app.models.ad_data import AdData
from app.auth.supabase_auth import supabase_service
from app.transformers.notion import NotionTransformer
from app.transformers.airtable import AirtableTransformer

class BuildService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    async def create_build(self, ad_data: AdData) -> Dict[str, Any]:
        """Save AdData to Supabase and return build info"""
        try:
            # Convert AdData to dict
            data = ad_data.to_dict()
            
            # Insert into Supabase
            response = supabase_service.table('ad_imports').insert(data).execute()
            
            if not response.data:
                raise Exception("No data returned from Supabase insert")
                
            result = response.data[0]
            self.logger.info(f"Created build for ad: {data['ad_name']}")
            
            return {
                "status": "success",
                "message": "Build created successfully",
                "build_id": data["build_id"],
                "ad_name": data["ad_name"],
                "ad_import_status": data["ad_import_status"]
            }
            
        except Exception as e:
            self.logger.error(f"Error creating build: {str(e)}")
            raise Exception(f"Error creating build: {str(e)}")
            
    async def process_notion_data(
        self, 
        payload: Dict[str, Any], 
        user_id: str,
        field_map: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Process Notion data and create build"""
        try:
            # Create NotionTransformer
            transformer = NotionTransformer(data=payload)
            
            # Transform to AdData
            ad_data = transformer.transform(user_id=user_id, field_map=field_map)
            
            # Create build
            return await self.create_build(ad_data)
            
        except Exception as e:
            self.logger.error(f"Error processing Notion data: {str(e)}")
            raise Exception(f"Error processing Notion data: {str(e)}")
            
    async def process_airtable_data(
        self, 
        payload: Dict[str, Any], 
        user_id: str,
        base_id: str, 
        table_id: str,
        field_map: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Process Airtable data and create build"""
        try:
            # Create AirtableTransformer
            transformer = AirtableTransformer(data=payload)
            
            # Transform to AdData
            ad_data = transformer.transform(
                user_id=user_id,
                base_id=base_id,
                table_id=table_id,
                field_map=field_map
            )
            
            # Create build
            return await self.create_build(ad_data)
            
        except Exception as e:
            self.logger.error(f"Error processing Airtable data: {str(e)}")
            raise Exception(f"Error processing Airtable data: {str(e)}") 