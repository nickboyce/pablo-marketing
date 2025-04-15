from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.auth.auth_utils import get_current_user
from app.services.api_key_service import ApiKeyService, generate_api_key_for_user
from app.auth.supabase_auth import supabase
import logging
from app.config import settings

router = APIRouter()
templates = Jinja2Templates(directory="templates")
logger = logging.getLogger(__name__)

api_key_service = ApiKeyService(supabase)

@router.get("/", response_class=HTMLResponse)
async def get_api_keys(request: Request, current_user = Depends(get_current_user)):
    """Get API keys management page"""
    keys = await api_key_service.list_keys(current_user.id)
    
    return templates.TemplateResponse(
        "api_keys.html", 
        {
            "request": request,
            "keys": keys
        }
    )

@router.post("/create")
async def create_api_key(
    request: Request,
    name: str = Form(...),
    current_user = Depends(get_current_user)
):
    """Create a new API key"""
    try:
        key_data = await api_key_service.create_api_key(current_user.id, name)
        return templates.TemplateResponse(
            "api_key_created.html",
            {
                "request": request,
                "key": key_data["key"],
                "name": key_data["name"]
            }
        )
    except Exception as e:
        logger.error(f"Error creating API key: {str(e)}")
        return RedirectResponse(
            url="/api-keys?message=Error creating API key&error=true",
            status_code=303
        )

@router.get("/delete/{key_id}")
async def delete_api_key(
    key_id: str,
    current_user = Depends(get_current_user)
):
    """Delete an API key"""
    try:
        await api_key_service.delete_key(current_user.id, key_id)
        return RedirectResponse(
            url="/api-keys?message=API key deleted successfully",
            status_code=303
        )
    except Exception as e:
        logger.error(f"Error deleting API key: {str(e)}")
        return RedirectResponse(
            url="/api-keys?message=Error deleting API key&error=true",
            status_code=303
        )

@router.get("/example")
async def example_route():
    return {
        "api_url": f"{settings.app_url}/api/v1",
        "webhook_url": f"{settings.app_url}/webhooks/notion"
    }

@router.post("/generate")
async def generate_key(request: Request, current_user = Depends(get_current_user)):
    """
    Generate a new API key for the current user.
    """
    try:
        api_key = await generate_api_key_for_user(current_user.id)
        logger.info(f"Successfully generated API key for user {current_user.id}")
        
        # Return the user to a 'key created' page or redirect
        return RedirectResponse(url="/api-keys?message=Key+Created", status_code=303)
    except Exception as e:
        logger.error(f"Error generating API key: {str(e)}")
        return RedirectResponse(url="/api-keys?message=Error+generating+API+key&error=true", status_code=303) 