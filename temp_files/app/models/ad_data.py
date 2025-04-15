from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from enum import Enum
import uuid

class MediaType(str, Enum):
    STATIC = "static"
    VIDEO = "video"

class ImportStatus(str, Enum):
    BUILDING = "building"
    COMPLETE = "complete"
    ERROR = "error"

class AdData(BaseModel):
    """Generic model for ad data to be saved to Supabase"""
    source_type: str = Field(..., description="Source of the ad data (e.g., 'notion', 'airtable')")
    source_record_id: str = Field(..., description="ID of the record in the source system")
    source_table_id: Optional[str] = Field(None, description="ID of the table in the source system (e.g., base_id_table_id for Airtable)")
    user_id: str = Field(..., description="ID of the user who owns this ad")
    build_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier for this build")
    ad_id: Optional[str] = Field(None, description="Optional ID of the ad in the destination system")
    ad_name: str = Field(..., min_length=1, description="Name of the ad")
    ad_headline: str = Field(..., min_length=1, description="Headline text for the ad")
    ad_body: str = Field(..., min_length=1, description="Body text for the ad")
    ad_link_url: HttpUrl = Field(..., description="URL the ad links to")
    ad_media_type: MediaType = Field(..., description="Type of media (static or video)")
    ad_cta_label: str = Field(..., min_length=1, description="Call to action button text")
    ad_asset_url: HttpUrl = Field(..., description="URL of the primary ad asset")
    ad_asset_filename: str = Field(..., min_length=1, description="Filename of the primary ad asset")
    ad_asset_vertical_url: Optional[HttpUrl] = Field(None, description="URL of the vertical ad asset")
    ad_asset_vertical_filename: Optional[str] = Field(None, description="Filename of the vertical ad asset")
    destination_ad_account_id: str = Field(..., min_length=1, description="Facebook ad account ID")
    destination_adset_id: str = Field(..., min_length=1, description="Facebook ad set ID")
    destination_template_ad_id: str = Field(..., min_length=1, description="Facebook template ad ID")
    ad_import_status: ImportStatus = Field(..., description="Status of the ad import process")

    def to_dict(self) -> Dict[str, Any]:
        """Convert the model to a dictionary with URLs as strings"""
        data = self.model_dump()
        # Convert HttpUrl objects to strings
        data['ad_link_url'] = str(data['ad_link_url'])
        data['ad_asset_url'] = str(data['ad_asset_url'])
        if data['ad_asset_vertical_url']:
            data['ad_asset_vertical_url'] = str(data['ad_asset_vertical_url'])
        return data

    class Config:
        json_schema_extra = {
            "example": {
                "source_type": "notion",
                "source_record_id": "123e4567-e89b-12d3-a456-426614174000",
                "user_id": "user123",
                "build_id": "550e8400-e29b-41d4-a716-446655440000",
                "ad_id": None,
                "ad_name": "example-ad",
                "ad_headline": "Amazing Product",
                "ad_body": "Buy now!",
                "ad_link_url": "https://example.com",
                "ad_media_type": "static",
                "ad_cta_label": "LEARN_MORE",
                "ad_asset_url": "https://example.com/image.jpg",
                "ad_asset_filename": "image.jpg",
                "ad_asset_vertical_url": "https://example.com/vertical.jpg",
                "ad_asset_vertical_filename": "vertical.jpg",
                "destination_ad_account_id": "1234567890",
                "destination_adset_id": "adset123",
                "destination_template_ad_id": "template123",
                "ad_import_status": "building"
            }
        } 