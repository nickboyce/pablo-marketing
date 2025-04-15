# app/dependencies.py
import logging
import json
from typing import Optional, Dict
from urllib.parse import unquote

from fastapi import Depends, HTTPException, status, Query

# Assuming these are the correct import paths based on previous context
from app.middleware.api_key_middleware import get_api_key_from_request
from app.auth.supabase_auth import supabase_service

logger = logging.getLogger(__name__)

async def verify_api_key_and_get_user(
    api_key: Optional[str] = Depends(get_api_key_from_request)
) -> str:
    """
    Dependency to verify the API key and return the associated user ID.
    Raises HTTPException 401 if the key is missing or invalid.
    """
    if not api_key:
        logger.error("API key verification failed: No API key provided.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key"
        )

    try:
        # Ensure we only select the user_id column for efficiency
        response = supabase_service.table("api_keys").select("user_id").eq("key", api_key).limit(1).execute()

        if not response.data:
            logger.error(f"API key verification failed: Invalid API key provided.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key"
            )

        user_id = response.data[0]["user_id"]
        logger.info(f"API key verified successfully for user_id: {user_id}")
        return user_id

    except Exception as e:
        logger.error(f"API key verification failed due to database error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not verify API key due to an internal error."
        )

async def parse_field_map(
    field_map: Optional[str] = Query(
        None,
        description='URL-encoded JSON string mapping source fields to destination fields. Example: {"Source Name":"ad_name"}'
    )
) -> Optional[Dict[str, str]]:
    """
    FastAPI dependency that parses a URL-encoded JSON field mapping.
    
    Args:
        field_map: The raw, URL-encoded JSON string from the query param
                  Example: {"Source Field":"dest_field"}
                  
    Returns:
        Dict mapping source fields to destination fields, or None if no mapping provided
        
    Raises:
        HTTPException: If the field_map is provided but invalid
    """
    if not field_map:
        return None

    try:
        # URL decode the string first
        decoded_string = unquote(field_map)
        logger.info(f"URL decoded field_map string: {decoded_string}")

        # Parse the decoded string as JSON
        mapping = json.loads(decoded_string)
        
        # Validate the mapping structure
        if not isinstance(mapping, dict):
            raise ValueError("Field map must be a JSON object")
            
        # Ensure all keys and values are strings
        invalid_entries = [
            (k, v) for k, v in mapping.items()
            if not isinstance(k, str) or not isinstance(v, str)
        ]
        if invalid_entries:
            raise ValueError(
                f"All keys and values must be strings. Invalid entries: {invalid_entries}"
            )

        logger.info(f"Successfully parsed field map: {mapping}")
        return mapping

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in field_map: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid JSON format in field_map: {str(e)}"
        )
    except ValueError as e:
        logger.error(f"Invalid field map structure: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error parsing field_map: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error processing field map"
        ) 