from .base import DataTransformer
from typing import Dict, Any, Optional
from app.models.ad_data import AdData
import logging
import json

logger = logging.getLogger(__name__)

class NotionTransformer(DataTransformer):
    def __init__(self, data: Dict[str, Any]):
        self.data = data
        # Log the entire incoming data structure
        logger.info(f"Initializing NotionTransformer with data: {json.dumps(self.data, indent=2)}")
        
    def get_property_value(self, property_name: str, field_map: Optional[Dict[str, str]] = None) -> Optional[str]:
        """Extract value from any Notion property type"""
        logger.info(f"\nExtracting property: {property_name}")
        
        # Properties are nested under data.properties in the Notion webhook payload
        all_properties = self.data.get('data', {}).get('properties', {})
        logger.info(f"All available properties: {list(all_properties.keys())}")
        
        # If field_map is provided, check if we need to use a different property name
        notion_property_name = property_name
        if field_map:
            # Look for a Notion property name that maps to our desired field
            for notion_name, mapped_name in field_map.items():
                if mapped_name == property_name:
                    logger.info(f"Using Notion property '{notion_name}' for field '{property_name}'")
                    notion_property_name = notion_name
                    break
        
        prop = all_properties.get(notion_property_name, {})
        if not prop:
            logger.warning(f"Property {notion_property_name} not found in Notion data")
            return None
            
        # Log the exact structure of this property
        logger.info(f"Structure of property {notion_property_name}:")
        logger.info(json.dumps(prop, indent=2))
            
        # Handle different property types
        property_type = None
        for key in ["rich_text", "select", "rollup", "url", "formula", "files"]:
            if key in prop:
                property_type = key
                break
        logger.info(f"Detected property type: {property_type}")
            
        if "rich_text" in prop:
            value = "".join(block.get("text", {}).get("content", "") for block in prop["rich_text"])
            logger.info(f"Extracted rich_text value: {value}")
            return value if value else None
        elif "select" in prop:
            value = prop["select"].get("name", "")
            logger.info(f"Extracted select value: {value}")
            return value if value else None
        elif "rollup" in prop:
            # Handle rollup of rich text
            if prop["rollup"].get("array"):
                value = "".join(
                    block.get("rich_text", [{}])[0].get("text", {}).get("content", "")
                    for block in prop["rollup"]["array"]
                )
                logger.info(f"Extracted rollup value: {value}")
                return value if value else None
            return None
        elif "url" in prop:
            value = prop["url"]
            logger.info(f"Found URL property value: {value}")
            if value and not value.startswith(('http://', 'https://')):
                value = f"https://{value}"
                logger.info(f"Added https:// prefix to URL: {value}")
            return value if value else None
        elif "formula" in prop:
            formula = prop["formula"]
            if formula.get("type") == "string":
                value = formula.get("string", "")
                logger.info(f"Extracted formula value: {value}")
                return value if value else None
        elif "files" in prop:
            logger.info("Processing files property:")
            logger.info(json.dumps(prop["files"], indent=2))
            
            files = prop["files"]
            if not files or len(files) == 0:
                logger.warning(f"No files found for property {notion_property_name}")
                return None
                
            file_obj = files[0]  # Get the first file
            logger.info(f"Processing first file object:")
            logger.info(json.dumps(file_obj, indent=2))
            
            # Get the file URL based on type
            file_type = file_obj.get("type")
            logger.info(f"File type: {file_type}")
            
            value = None
            if file_type == "file":
                # Internal Notion file
                file_data = file_obj.get("file", {})
                logger.info(f"Internal file data: {file_data}")
                value = file_data.get("url")
                logger.info(f"Found internal Notion file URL: {value}")
            elif file_type == "external":
                # External file
                external_data = file_obj.get("external", {})
                logger.info(f"External file data: {external_data}")
                value = external_data.get("url")
                logger.info(f"Found external file URL: {value}")
            else:
                logger.warning(f"Unknown file type '{file_type}' for property {notion_property_name}")
                logger.info(f"Full file object for unknown type:")
                logger.info(json.dumps(file_obj, indent=2))
                return None
            
            if value and not value.startswith(('http://', 'https://')):
                value = f"https://{value}"
                logger.info(f"Added https:// prefix to file URL: {value}")
            
            if not value:
                logger.warning(f"No URL found in file object for {notion_property_name}")
            else:
                logger.info(f"Final URL value: {value}")
            
            return value if value else None
            
        logger.warning(f"Unhandled property type for {notion_property_name}")
        return None
        
    def transform(self, user_id: str, field_map: Optional[Dict[str, str]] = None) -> AdData:
        """Transform Notion data into AdData"""
        logger.info("\nStarting Notion data transformation")
        logger.info(f"User ID: {user_id}")
        logger.info(f"Field map: {field_map}")
        
        # Get the asset URLs first
        logger.info("\nExtracting ad_asset URL:")
        ad_asset_url = self.get_property_value("ad_asset", field_map)
        logger.info(f"Extracted ad_asset_url: {ad_asset_url}")
        
        logger.info("\nExtracting ad_asset_vertical URL:")
        ad_asset_vertical_url = self.get_property_value("ad_asset_vertical", field_map)
        logger.info(f"Extracted ad_asset_vertical_url: {ad_asset_vertical_url}")

        # Extract filenames from URLs
        if not ad_asset_url:
            logger.error("ad_asset URL is missing")
            raise ValueError("ad_asset is required and must be a valid URL")
        
        try:
            logger.info(f"\nExtracting filename from ad_asset URL: {ad_asset_url}")
            ad_asset_filename = self.extract_filename(ad_asset_url)
            if not ad_asset_filename:
                logger.error(f"Could not extract filename from ad_asset URL: {ad_asset_url}")
                raise ValueError(f"Could not extract filename from ad_asset URL: {ad_asset_url}")
            logger.info(f"Extracted ad_asset filename: {ad_asset_filename}")
        except Exception as e:
            logger.error(f"Error extracting ad_asset filename: {str(e)}")
            raise ValueError(f"Could not extract filename from ad_asset URL: {str(e)}")

        ad_asset_vertical_filename = None
        if ad_asset_vertical_url:
            try:
                logger.info(f"\nExtracting filename from ad_asset_vertical URL: {ad_asset_vertical_url}")
                ad_asset_vertical_filename = self.extract_filename(ad_asset_vertical_url)
                logger.info(f"Extracted ad_asset_vertical filename: {ad_asset_vertical_filename}")
            except Exception as e:
                logger.warning(f"Could not extract filename from ad_asset_vertical URL: {str(e)}")

        try:
            logger.info("\nCreating AdData object")
            ad_data = AdData(
                source_type="notion",
                source_record_id=self.data.get('data', {}).get('id'),
                user_id=user_id,
                ad_id=self.get_property_value("ad_id", field_map),
                ad_name=self.get_property_value("ad_name", field_map),
                ad_headline=self.get_property_value("ad_headline", field_map),
                ad_body=self.get_property_value("ad_body", field_map),
                ad_link_url=self.get_property_value("ad_link", field_map),
                ad_media_type=self.get_property_value("ad_media_type", field_map),
                ad_cta_label=self.get_property_value("ad_cta_label", field_map),
                ad_asset_url=ad_asset_url,
                ad_asset_filename=ad_asset_filename,
                ad_asset_vertical_url=ad_asset_vertical_url,
                ad_asset_vertical_filename=ad_asset_vertical_filename,
                destination_ad_account_id=self.get_property_value("destination_ad_account_id", field_map),
                destination_adset_id=self.get_property_value("destination_adset_id", field_map),
                destination_template_ad_id=self.get_property_value("destination_template_ad_id", field_map),
                ad_import_status="building",
                source_table_id=self.data.get('data', {}).get('parent', {}).get('database_id')
            )
            logger.info("Successfully created AdData object")
            return ad_data
        except Exception as e:
            logger.error(f"Failed to create AdData object: {str(e)}")
            raise 