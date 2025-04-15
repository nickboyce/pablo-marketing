from .base import DataTransformer
from typing import Dict, Any, Optional
from app.models.ad_data import AdData
import logging
import json
from pydantic import HttpUrl

logger = logging.getLogger(__name__)

class AirtableTransformer(DataTransformer):
    def __init__(self, data: Dict[str, Any]):
        self.data = data
        # Log the entire incoming data structure
        logger.info(f"Initializing AirtableTransformer with data: {json.dumps(self.data, indent=2)}")
        
    def get_field_value(self, field_name: str, field_map: Optional[Dict[str, str]] = None) -> Optional[Any]:
        """Extract value from Airtable fields"""
        logger.info(f"\nExtracting field: {field_name}")
        
        fields = self.data.get('fields', {})
        logger.info(f"All available fields: {list(fields.keys())}")
        
        # If field_map is provided, check if we need to use a different field name
        airtable_field_name = field_name
        if field_map:
            # Look for an Airtable field name that maps to our desired field
            for source_name, mapped_name in field_map.items():
                if mapped_name == field_name:
                    logger.info(f"Using Airtable field '{source_name}' for field '{field_name}'")
                    airtable_field_name = source_name
                    break
        
        value = fields.get(airtable_field_name)
        logger.info(f"Raw value for {airtable_field_name}: {value}")
        
        if value is None:
            logger.warning(f"Field {airtable_field_name} not found in Airtable data")
            return None
            
        # Handle file fields
        if field_name in ["ad_asset", "ad_asset_vertical"] and isinstance(value, list) and value:
            logger.info(f"Processing file field {airtable_field_name}:")
            logger.info(json.dumps(value, indent=2))
            
            file_obj = value[0]
            logger.info(f"Processing first file object:")
            logger.info(json.dumps(file_obj, indent=2))
            
            if isinstance(file_obj, dict) and "url" in file_obj:
                result = {
                    "url": file_obj["url"],
                    "filename": file_obj.get("filename")
                }
                logger.info(f"Extracted file data: {result}")
                return result
            logger.warning(f"Invalid file object structure for {airtable_field_name}")
            return None
            
        # If it's a list, take the first item
        if isinstance(value, list):
            logger.info(f"Field {airtable_field_name} is a list, taking first item")
            return value[0] if value else None
            
        return value
        
    def transform(self, user_id: str, base_id: str = None, table_id: str = None, field_map: Optional[Dict[str, str]] = None) -> AdData:
        """Transform Airtable data into AdData"""
        logger.info("\nStarting Airtable data transformation")
        logger.info(f"User ID: {user_id}")
        logger.info(f"Base ID: {base_id}")
        logger.info(f"Table ID: {table_id}")
        logger.info(f"Field map: {field_map}")
        
        # Create source_table_id from base_id and table_id
        source_table_id = None
        if base_id and table_id:
            source_table_id = f"{base_id}_{table_id}"
        logger.info(f"Source table ID: {source_table_id}")
        
        # Get all field values, handling arrays appropriately
        fields = {}
        required_fields = [
            "ad_name", "ad_headline", "ad_body", "ad_link", "ad_media_type",
            "ad_cta_label", "ad_asset", "ad_asset_vertical",
            "destination_ad_account_id", "destination_adset_id", "destination_template_ad_id"
        ]
        
        optional_fields = ["ad_id"]
        
        # Process required fields
        logger.info("\nProcessing required fields:")
        for field_name in required_fields:
            value = self.get_field_value(field_name, field_map)
            if value is not None:
                fields[field_name] = value
                logger.info(f"Got value for {field_name}: {value}")
            else:
                logger.warning(f"Missing required field: {field_name}")
                
        # Process optional fields
        logger.info("\nProcessing optional fields:")
        for field_name in optional_fields:
            value = self.get_field_value(field_name, field_map)
            if value is not None:
                fields[field_name] = value
                logger.info(f"Got value for {field_name}: {value}")

        # Convert URL strings to HttpUrl objects
        url_fields = {
            "ad_link": "ad_link_url",
            "ad_asset": "ad_asset_url",
            "ad_asset_vertical": "ad_asset_vertical_url"
        }

        logger.info("\nProcessing URL fields:")
        for airtable_field, ad_field in url_fields.items():
            if airtable_field in fields and fields[airtable_field]:
                logger.info(f"\nProcessing URL field {airtable_field}:")
                logger.info(f"Raw value: {fields[airtable_field]}")
                
                if isinstance(fields[airtable_field], dict):
                    url_value = fields[airtable_field]["url"]
                    logger.info(f"Extracted URL from dict: {url_value}")
                    # Store filename if available
                    if "filename" in fields[airtable_field]:
                        filename = fields[airtable_field]["filename"]
                        fields[f"{ad_field.replace('_url', '_filename')}"] = filename
                        logger.info(f"Stored filename: {filename}")
                else:
                    url_value = fields[airtable_field]
                    logger.info(f"Using direct URL value: {url_value}")
                
                try:
                    fields[ad_field] = HttpUrl(url_value)
                    logger.info(f"Successfully validated URL for {ad_field}")
                except ValueError as e:
                    logger.error(f"Invalid URL for {airtable_field}: {url_value}")
                    logger.error(f"Validation error: {str(e)}")
                    raise ValueError(f"Invalid URL for {airtable_field}: {str(e)}")

        # Create AdData with only the fields we have
        try:
            logger.info("\nCreating AdData object")
            ad_data = AdData(
                source_type="airtable",
                source_record_id=self.data.get('id'),
                source_table_id=source_table_id,
                user_id=user_id,
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
            logger.info("Successfully created AdData object")
            return ad_data
        except Exception as e:
            logger.error(f"Failed to create AdData: {str(e)}")
            raise 