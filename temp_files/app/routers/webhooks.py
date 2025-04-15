from fastapi import APIRouter, Request, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any
# Remove the direct import of get_api_key_from_request if no longer needed elsewhere
# from app.middleware.api_key_middleware import get_api_key_from_request
from app.auth.supabase_auth import supabase_service
from app.services import build_service
from app.models import NotionPayload, AdData, AirtablePayload
from app.services.airtable_service import AirtableService
from app.services.connection_service import connection_service
from pydantic import ValidationError
# Import the new dependency
from app.dependencies import verify_api_key_and_get_user, parse_field_map

# Try to import NotionService, but provide a fallback
try:
    from app.services.notion_service import NotionService
    NOTION_SERVICE_AVAILABLE = True
except ImportError as e:
    NOTION_SERVICE_AVAILABLE = False
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"Notion service not available: {str(e)}. Notion webhooks will be logged but not processed.")

import logging
import json
import os
from datetime import datetime

router = APIRouter()
logger = logging.getLogger(__name__)

def pretty_json(obj):
    """Format object as pretty JSON string"""
    return json.dumps(obj, indent=2, sort_keys=True, default=str)

def save_webhook_to_file(payload: dict, prefix: str):
    """Save webhook payload to a file for debugging"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"logs/{prefix}_{timestamp}.json"
    os.makedirs("logs", exist_ok=True)
    with open(filename, "w") as f:
        json.dump(payload, f, indent=2)
    logger.info(f"Saved webhook payload to {filename}")

@router.post("/notion")
@router.get("/notion")
async def notion_webhook(
    request: Request, 
    user_id: str = Depends(verify_api_key_and_get_user),
    field_map: Optional[Dict[str, str]] = Depends(parse_field_map)
):
    """Handle webhook from Notion"""
    try:
        # Log the request
        logger.info(f"Received request for /notion {request.method} from user_id: {user_id}")
        logger.info(f"Field map: {field_map}")
        
        # Handle GET request from Notion verification
        if request.method == "GET":
            # Return 200 OK to confirm the endpoint is working
            return {"status": "success", "message": "Notion webhook endpoint is active"}
        
        # --- Remove API key validation block --- 
        # if not api_key: ...
        # response = supabase_service.table(...) ...
        # user_id = response.data[0]["user_id"]
        
        # Get the payload from the request body (POST only)
        payload = await request.json()
        
        # Save to file for debugging
        save_webhook_to_file(payload, "notion")
        
        # Process the data using build service
        result = await build_service.process_notion_data(payload, user_id, field_map)
        
        return result
        
    except HTTPException as e:
        # Re-raise HTTP exceptions (like 401 from the dependency)
        raise
    except ValueError as e:
        # Return 400 for validation errors
        logger.error(f"Validation error in Notion webhook: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"status": "error", "message": str(e)}
        )
    except Exception as e:
        # Return 500 for other errors
        logger.error(f"Error processing Notion webhook: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"status": "error", "message": "Internal server error processing webhook"}
        )

@router.post("/airtable")
@router.get("/airtable")
async def airtable_webhook(
    request: Request,
    source_record_id: Optional[str] = Query(None, alias="source_record_id"),
    source_table_id: Optional[str] = Query(None, alias="source_table_id"),
    user_id: str = Depends(verify_api_key_and_get_user),
    field_map: Optional[Dict[str, str]] = Depends(parse_field_map)
):
    """Handle webhook from Airtable"""
    try:
        # Log the request
        logger.info(f"Received request for /airtable {request.method} from user_id: {user_id}")
        logger.info(f"Query params: source_record_id={source_record_id}, source_table_id={source_table_id}")
        logger.info(f"Field map: {field_map}")
        
        # Parse table ID into base_id and table_id
        if not source_table_id:
            logger.error("Missing source_table_id for airtable webhook")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Missing source_table_id parameter"
            )
            
        # source_table_id format: appXXX_tblYYY
        try:
            base_id, table_id = source_table_id.split("_")
            logger.info(f"Parsed source_table_id: base_id={base_id}, table_id={table_id}")
        except ValueError:
            logger.error(f"Invalid source_table_id format: {source_table_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid source_table_id format. Expected format: base_id_table_id"
            )
            
        # Get the Airtable service for this user
        try:
            airtable_service = await connection_service.get_airtable_service(user_id)
            if not airtable_service:
                raise Exception("No Airtable connection found for user")
        except Exception as e:
            logger.error(f"Failed to get Airtable service: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get Airtable service: {str(e)}"
            )
            
        # Get the payload
        if request.method == "GET":
            logger.info("GET request - fetching record from Airtable")
            if not source_record_id:
                logger.error("Missing source_record_id for GET request")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Missing source_record_id parameter"
                )
            
            try:
                record = await airtable_service.get_record(base_id, table_id, source_record_id)
                logger.info(f"Fetched record from Airtable: {json.dumps(record, indent=2)}")
                payload = record
            except Exception as e:
                logger.error(f"Failed to fetch record from Airtable: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to fetch record from Airtable: {str(e)}"
                )
        else: # POST request
            logger.info("POST request - getting payload from body")
            try:
                payload = await request.json()
            except Exception as e:
                logger.error(f"Failed to parse request body: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid JSON in request body"
                )
        
        save_webhook_to_file(payload, "airtable")
        
        logger.info("Processing data with build service")
        result = await build_service.process_airtable_data(
            payload, user_id, base_id, table_id, field_map
        )
        
        return result
        
    except HTTPException as e:
        # Re-raise HTTP exceptions
        raise
    except ValueError as e:
        # Return 400 for validation errors
        logger.error(f"Validation error in Airtable webhook: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"status": "error", "message": str(e)}
        )
    except Exception as e:
        # Return 500 for other errors
        logger.error(f"Error processing Airtable webhook: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"status": "error", "message": "Internal server error processing webhook"}
        ) 