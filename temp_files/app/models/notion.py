from pydantic import BaseModel, Field, validator, HttpUrl
from typing import Optional, List, Dict, Any
from .ad_data import AdData
import logging
import re
from urllib.parse import urlparse, unquote
import json

logger = logging.getLogger(__name__)

class NotionPayload(BaseModel):
    """Schema for raw Notion data"""
    data: Dict[str, Any] = Field(..., description="The Notion page data")
    source: Dict[str, Any] = Field(..., description="The data source information")

    @staticmethod
    def extract_filename_from_url(url: str) -> str:
        """Extract filename from a URL, handling various URL formats including S3 URLs with query parameters"""
        # Parse the URL
        parsed = urlparse(url)
        # Get the path part
        path = unquote(parsed.path)
        # Split on / and get the last part
        filename = path.split('/')[-1]
        
        # If filename is empty or doesn't have an extension, try to find it in the URL
        if not filename or '.' not in filename:
            # Look for a filename pattern in the entire URL
            match = re.search(r'/([^/?]+\.[^/?]+)', url)
            if match:
                filename = match.group(1)
            else:
                raise ValueError(f"Could not extract filename from URL: {url}")
        
        return filename

    @validator('data')
    def validate_data(cls, v):
        """Validate the Notion page data structure"""
        if not v.get('id'):
            raise ValueError("Missing page ID in data")
        if not v.get('properties'):
            raise ValueError("Missing properties in data")
        
        # Extract database_id from parent object
        parent = v.get('parent', {})
        if parent.get('type') == 'database_id':
            v['database_id'] = parent.get('database_id')
            
        return v

    def get_property_value(self, property_name: str) -> Optional[str]:
        """Extract value from any Notion property type"""
        prop = self.data.get('properties', {}).get(property_name, {})
        if not prop:
            return None
            
        # Handle different property types
        if "rich_text" in prop:
            value = "".join(block.get("text", {}).get("content", "") for block in prop["rich_text"])
            return value if value else None
        elif "select" in prop:
            value = prop["select"].get("name", "")
            return value if value else None
        elif "rollup" in prop:
            # Handle rollup of rich text
            if prop["rollup"].get("array"):
                value = "".join(
                    block.get("rich_text", [{}])[0].get("text", {}).get("content", "")
                    for block in prop["rollup"]["array"]
                )
                return value if value else None
            return None
        elif "url" in prop:
            value = prop["url"]
            if value and not value.startswith(('http://', 'https://')):
                value = f"https://{value}"
            return value if value else None
        elif "formula" in prop:
            formula = prop["formula"]
            if formula.get("type") == "string":
                value = formula.get("string", "")
                return value if value else None
        elif "files" in prop:
            files = prop["files"]
            if files and len(files) > 0:
                value = files[0].get("file", {}).get("url", "")
                if value and not value.startswith(('http://', 'https://')):
                    value = f"https://{value}"
                return value if value else None
        return None

    def to_ad_data(self, supabase_user_id: str) -> AdData:
        """Transform Notion data into AdData"""
        # logger.info(f"Converting Notion payload to AdData: {json.dumps(self.data, indent=2)}")
        
        # Get the asset URLs first
        ad_asset_url = self.get_property_value("ad_asset")
        ad_asset_vertical_url = self.get_property_value("ad_asset_vertical")

        # Extract filenames from URLs
        if not ad_asset_url:
            raise ValueError("ad_asset is required and must be a valid URL")
        
        try:
            ad_asset_filename = self.extract_filename_from_url(ad_asset_url)
        except ValueError as e:
            raise ValueError(f"Could not extract filename from ad_asset URL: {str(e)}")

        ad_asset_vertical_filename = None
        if ad_asset_vertical_url:
            try:
                ad_asset_vertical_filename = self.extract_filename_from_url(ad_asset_vertical_url)
            except ValueError as e:
                logger.warning(f"Could not extract filename from ad_asset_vertical URL: {str(e)}")

        return AdData(
            source_type="notion",
            source_record_id=self.data.get('id'),
            user_id=supabase_user_id,
            ad_id=self.get_property_value("ad_id"),
            ad_name=self.get_property_value("ad_name"),
            ad_headline=self.get_property_value("ad_headline"),
            ad_body=self.get_property_value("ad_body"),
            ad_link_url=self.get_property_value("ad_link"),
            ad_media_type=self.get_property_value("ad_media_type"),
            ad_cta_label=self.get_property_value("ad_cta_label"),
            ad_asset_url=ad_asset_url,
            ad_asset_filename=ad_asset_filename,
            ad_asset_vertical_url=ad_asset_vertical_url,
            ad_asset_vertical_filename=ad_asset_vertical_filename,
            destination_ad_account_id=self.get_property_value("destination_ad_account_id"),
            destination_adset_id=self.get_property_value("destination_adset_id"),
            destination_template_ad_id=self.get_property_value("destination_template_ad_id"),
            ad_import_status="building",
            source_table_id=self.data.get('database_id')
        )

    class Config:
        json_schema_extra = {
            "example": {
                "data": {
                    "id": "1c1d8901-aa27-8037-a3f3-ee806cb44400",
                    "properties": {
                        "ad_name": {
                            "type": "formula",
                            "formula": {
                                "type": "string",
                                "string": "example-ad"
                            }
                        },
                        "ad_asset_headline": {
                            "type": "rich_text",
                            "rich_text": [
                                {
                                    "annotations": {"bold": False},
                                    "plain_text": "Amazing Product",
                                    "text": {"content": "Amazing Product"}
                                }
                            ]
                        }
                    }
                },
                "source": {
                    "type": "automation",
                    "user_id": "user123"
                }
            }
        } 