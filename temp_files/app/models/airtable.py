from pydantic import BaseModel, Field, validator, HttpUrl
from typing import Optional, Dict, Any, List
from .ad_data import AdData
import logging

logger = logging.getLogger(__name__)

class AirtablePayload(BaseModel):
    """Schema for raw Airtable data"""
    data: Dict[str, Any] = Field(..., description="The Airtable record data")
    source: Dict[str, Any] = Field(..., description="The data source information")

    @validator('data')
    def validate_data(cls, v):
        """Validate the Airtable record data structure"""
        if not v.get('recordId'):
            raise ValueError("Missing record ID in data")
        if not v.get('fields'):
            raise ValueError("Missing fields in data")
        return v

    def get_field_value(self, field_name: str) -> Optional[Any]:
        """Extract value from Airtable fields, handling both single values and arrays"""
        fields = self.data.get('fields', {})
        value = fields.get(field_name)
        
        if value is None:
            return None
            
        # Handle file fields (ad_asset and ad_asset_vertical)
        if field_name in ["ad_asset", "ad_asset_vertical"] and isinstance(value, list) and value:
            file_obj = value[0]
            if isinstance(file_obj, dict) and "url" in file_obj:
                return {
                    "url": file_obj["url"],
                    "filename": file_obj.get("filename")
                }
            return None
            
        # If it's a list, take the first item
        if isinstance(value, list):
            return value[0] if value else None
            
        return value

    def to_ad_data(self, supabase_user_id: str, base_id: str = None, table_id: str = None) -> AdData:
        """Transform Airtable data into AdData"""
        # Create source_table_id from base_id and table_id
        source_table_id = None
        if base_id and table_id:
            source_table_id = f"{base_id}_{table_id}"
        
        # Get all field values, handling arrays appropriately
        fields = {}
        required_fields = [
            "ad_name", "ad_headline", "ad_body", "ad_link", "ad_media_type",
            "ad_cta_label", "ad_asset", "ad_asset_vertical",
            "destination_ad_account_id", "destination_adset_id", "destination_template_ad_id"
        ]
        
        optional_fields = ["ad_id"]  # Optional fields that we'll include if present
        
        # Process required fields
        for field_name in required_fields:
            value = self.get_field_value(field_name)
            if value is not None:
                fields[field_name] = value
                
        # Process optional fields
        for field_name in optional_fields:
            value = self.get_field_value(field_name)
            if value is not None:
                fields[field_name] = value

        # Convert URL strings to HttpUrl objects
        url_fields = {
            "ad_link": "ad_link_url",
            "ad_asset": "ad_asset_url",
            "ad_asset_vertical": "ad_asset_vertical_url"
        }

        for airtable_field, ad_field in url_fields.items():
            if airtable_field in fields and fields[airtable_field]:
                if isinstance(fields[airtable_field], dict):
                    url_value = fields[airtable_field]["url"]
                    # Store filename if available
                    if "filename" in fields[airtable_field]:
                        fields[f"{ad_field.replace('_url', '_filename')}"] = fields[airtable_field]["filename"]
                else:
                    url_value = fields[airtable_field]
                
                try:
                    fields[ad_field] = HttpUrl(url_value)
                except ValueError as e:
                    logger.error(f"Invalid URL for {airtable_field}: {url_value}")
                    raise ValueError(f"Invalid URL for {airtable_field}: {str(e)}")

        # Create AdData with only the fields we have
        try:
            ad_data = AdData(
                source_type="airtable",
                source_record_id=self.data.get('recordId'),
                source_table_id=source_table_id,
                user_id=supabase_user_id,
                ad_id=fields.get("ad_id"),
                ad_name=fields.get("ad_name"),
                ad_headline=fields.get("ad_headline"),
                ad_body=fields.get("ad_body"),
                ad_link_url=fields.get("ad_link_url"),
                ad_media_type=fields.get("ad_media_type"),
                ad_cta_label=fields.get("ad_cta_label"),
                ad_asset_url=fields.get("ad_asset_url"),
                ad_asset_filename=fields.get("ad_asset_filename"),
                ad_asset_vertical_url=fields.get("ad_asset_vertical_url"),
                ad_asset_vertical_filename=fields.get("ad_asset_vertical_filename"),
                destination_ad_account_id=str(fields.get("destination_ad_account_id")) if fields.get("destination_ad_account_id") else None,
                destination_adset_id=str(fields.get("destination_adset_id")) if fields.get("destination_adset_id") else None,
                destination_template_ad_id=str(fields.get("destination_template_ad_id")) if fields.get("destination_template_ad_id") else None,
                ad_import_status="building"
            )
            return ad_data
        except Exception as e:
            logger.error(f"Failed to create AdData: {str(e)}")
            raise

    class Config:
        json_schema_extra = {
            "example": {
                "data": {
                    "recordId": "rec123",
                    "fields": {
                        "ad_name": "example-ad",
                        "ad_headline": "Amazing Product",
                        "ad_body": "Buy now!",
                        "ad_link": "https://example.com",
                        "ad_media_type": "static",
                        "ad_cta_label": "LEARN_MORE",
                        "ad_asset": "https://example.com/image.jpg",
                        "ad_asset_vertical": "https://example.com/vertical.jpg"
                    }
                },
                "source": {
                    "type": "automation",
                    "user_id": "user123"
                }
            }
        } 