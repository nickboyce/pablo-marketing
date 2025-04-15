from fastapi import Request, HTTPException, Depends, Query
from fastapi.security.api_key import APIKeyHeader
from app.services.api_key_service import ApiKeyService
from app.auth.supabase_auth import supabase
import logging

api_key_service = ApiKeyService(supabase)
API_KEY_HEADER = APIKeyHeader(name="X-API-Key")

logger = logging.getLogger(__name__)

async def get_api_key(api_key: str = Depends(API_KEY_HEADER)):
    user_id = await api_key_service.validate_key(api_key)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return user_id

async def get_api_key_from_request(
    request: Request,
    api_key_query: str = Query(None, alias="api_key")
) -> str:
    """Get API key from header or query parameter
    
    Args:
        request: The FastAPI request object
        api_key_query: Optional API key from query parameter
        
    Returns:
        The API key string
        
    Raises:
        HTTPException: If no API key is found
    """
    # First check header
    api_key_header = request.headers.get("X-API-Key")
    
    # Then check query parameter
    api_key = api_key_header or api_key_query
    
    if not api_key:
        logger.error("No API key found in header or query parameters")
        raise HTTPException(status_code=401, detail="API key is required")
    
    logger.info(f"API key received from {'header' if api_key_header else 'query'}: {api_key[:8]}...")
    
    return api_key 