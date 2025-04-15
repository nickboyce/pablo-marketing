from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/privacy-policy", response_class=HTMLResponse)
async def privacy_policy(request: Request):
    """Display the privacy policy"""
    return templates.TemplateResponse(
        "privacy_policy.html",
        {
            "request": request,
            "current_date": datetime.now().strftime("%B %d, %Y")
        }
    )

@router.get("/terms-of-service", response_class=HTMLResponse)
async def terms_of_service(request: Request):
    """Display the terms of service"""
    return templates.TemplateResponse(
        "terms_of_use.html",
        {
            "request": request,
            "current_date": datetime.now().strftime("%B %d, %Y")
        }
    ) 