from fastapi import APIRouter, Request, Form, Depends, HTTPException, Response, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.auth.supabase_auth import supabase, register_user, login_user, logout_user
from app.auth.auth_utils import set_auth_cookies, clear_auth_cookies
import logging
from app.config import get_settings
import httpx
from app.services.api_key_service import generate_api_key_for_user, api_key_service

router = APIRouter()
templates = Jinja2Templates(directory="templates")
settings = get_settings()
logger = logging.getLogger(__name__)

@router.post("/register")
async def register(
    request: Request, 
    email: str = Form(...), 
    password: str = Form(...), 
    password_confirm: str = Form(...),
    terms_accepted: bool = Form(False),
    cf_turnstile_response: str = Form(None)
):
    """Register a new user"""
    logger.info(f"Processing registration form for email: {email}")
    
    # Check if passwords match
    if password != password_confirm:
        logger.warning("Password mismatch during registration")
        return templates.TemplateResponse(
            "register.html", 
            {"request": request, "error": "Passwords do not match"}
        )
    
    # Verify with Cloudflare API
    turnstile_secret_key = settings.cloudflare_turnstile_secret_key
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://challenges.cloudflare.com/turnstile/v0/siteverify",
            data={
                "secret": turnstile_secret_key,
                "response": cf_turnstile_response,
                "remoteip": request.client.host
            }
        )
        
        result = response.json()
        if not result.get("success", False):
            logger.error(f"Turnstile verification failed: {result}")
            return templates.TemplateResponse(
                "register.html", 
                {
                    "request": request, 
                    "error": "CAPTCHA verification failed", 
                    "settings": settings,
                    "cloudflare_turnstile_site_key": settings.cloudflare_turnstile_site_key
                }
            )
        
        logger.info("Turnstile verification successful")

    try:
        logger.debug("Calling register_user function")
        response = await register_user(email, password)
        logger.info(f"Registration successful, user_id: {response.user.id if response.user else 'None'}")
        
        # Show confirmation needed page
        logger.debug("Showing email confirmation page")
        return templates.TemplateResponse(
            "confirmation_needed.html",
            {
                "request": request,
                "email": email
            }
        )
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        logger.exception("Registration exception details:")
        
        # Return error message to the template
        return templates.TemplateResponse(
            "register.html", 
            {
                "request": request, 
                "error": f"Registration failed: {str(e)}", 
                "email": email,
                "settings": settings
            }
        )

@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Show the registration form"""
    # Make sure settings is directly exposed from state
    settings_from_state = getattr(request.state, "settings", None)
    
    # Direct debug to see if settings is available
    if settings_from_state:
        logger.info("Settings available from middleware")
    else:
        logger.warning("Settings NOT available from middleware, using module settings")
    
    # Use both the middleware settings and direct settings to be safe
    return templates.TemplateResponse(
        "register.html", 
        {
            "request": request,
            "settings": settings_from_state or settings,
            "SUPABASE_URL": settings.SUPABASE_URL,
            "SUPABASE_KEY": settings.SUPABASE_KEY
        }
    )

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, message: str = None):
    """Show the login form"""
    logger.info("Rendering login page")
    # Make sure settings is directly exposed from state
    settings_from_state = getattr(request.state, "settings", None)
    
    # Log Turnstile site key for debugging
    logger.debug(f"Turnstile site key exists: {bool(settings.cloudflare_turnstile_site_key)}")
    
    return templates.TemplateResponse(
        "login.html", 
        {
            "request": request, 
            "message": message,
            "settings": settings_from_state or settings
        }
    )

@router.post("/login")
async def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    cf_turnstile_response: str = Form(None)
):
    """Process login form submission"""
    logger.info(f"Processing login form for email: {email}")
    
    # Verify with Cloudflare API
    turnstile_secret_key = settings.cloudflare_turnstile_secret_key
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://challenges.cloudflare.com/turnstile/v0/siteverify",
            data={
                "secret": turnstile_secret_key,
                "response": cf_turnstile_response,
                "remoteip": request.client.host
            }
        )
        
        result = response.json()
        if not result.get("success", False):
            logger.error(f"Turnstile verification failed: {result}")
            return templates.TemplateResponse(
                "login.html", 
                {
                    "request": request, 
                    "error": "CAPTCHA verification failed", 
                    "settings": settings,
                    "email": email
                }
            )
        
        logger.info("Turnstile verification successful")
    
    try:
        logger.debug("Calling login_user function")
        response = await login_user(email, password)
        
        if not response.user:
            logger.warning(f"Login failed for {email}: No user in response")
            return templates.TemplateResponse(
                "login.html", 
                {
                    "request": request, 
                    "error": "Invalid login credentials", 
                    "email": email,
                    "settings": settings
                }
            )
        
        logger.info(f"User logged in: {response.user.id}")
        
        # Check if user already has an API key
        keys = await api_key_service.list_keys(response.user.id)
        if not keys:
            # Generate an API key for the user if they don't have one
            try:
                await generate_api_key_for_user(response.user.id)
                logger.info(f"Generated initial API key for user {response.user.id}")
            except Exception as e:
                logger.error(f"Failed to generate initial API key: {str(e)}")
        
        # Set cookies and redirect
        redirect = RedirectResponse(url="/connections/", status_code=302)
        set_auth_cookies(redirect, response.session)
        
        logger.debug("Auth cookies set, redirecting to home page")
        return redirect
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        logger.exception("Login exception details:")
        return templates.TemplateResponse(
            "login.html", 
            {
                "request": request, 
                "error": f"Login failed: {str(e)}",
                "email": email,
                "settings": settings
            }
        )

@router.get("/logout")
async def logout_route(request: Request):
    """Log out the current user"""
    logger.info("Processing logout request")
    try:
        await logout_user(request)
        
        # Clear cookies and redirect to login
        redirect = RedirectResponse(url="/auth/login", status_code=303)
        clear_auth_cookies(redirect)
        return redirect
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        return RedirectResponse(url="/auth/login?error=Logout failed", status_code=303) 