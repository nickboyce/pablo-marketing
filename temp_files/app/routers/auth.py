from fastapi import APIRouter, Request, Form, HTTPException, Response, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.auth.supabase_auth import register_user, login_user, logout_user, supabase
from app.config import settings
import logging

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    logger.info("Rendering registration page")
    return templates.TemplateResponse("register.html", {"request": request})

@router.post("/register")
async def register(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    password_confirm: str = Form(...),
    name: str = Form(None)
):
    logger.info(f"Processing registration form for email: {email}")
    
    # Check if passwords match
    if password != password_confirm:
        logger.warning("Password mismatch during registration")
        return templates.TemplateResponse(
            "register.html", 
            {"request": request, "error": "Passwords do not match"}
        )
    
    try:
        logger.debug("Calling register_user function")
        response = await register_user(email, password, name)
        logger.info(f"Registration successful, user_id: {response.user.id if response.user else 'None'}")
        
        # Set cookies and redirect
        logger.debug("Setting auth cookies and redirecting to login")
        redirect = RedirectResponse(url="/auth/login?message=Registration successful! Please log in.", status_code=303)
        return redirect
    except HTTPException as e:
        logger.error(f"Registration HTTP exception: {e.detail}")
        return templates.TemplateResponse(
            "register.html", 
            {"request": request, "error": e.detail}
        )
    except Exception as e:
        logger.error(f"Unexpected registration error: {str(e)}")
        logger.exception("Registration exception details:")
        return templates.TemplateResponse(
            "register.html", 
            {"request": request, "error": f"Registration failed: {str(e)}"}
        )

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, message: str = None):
    logger.info("Rendering login page")
    return templates.TemplateResponse("login.html", {"request": request, "message": message})

@router.post("/login")
async def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...)
):
    logger.info(f"Processing login form for email: {email}")
    try:
        logger.debug("Calling login_user function")
        response = await login_user(email, password)
        logger.info(f"Login successful, setting cookies")
        
        # Set cookies and redirect
        redirect = RedirectResponse(url="/", status_code=303)
        redirect.set_cookie(
            key="access_token",
            value=response.session.access_token,
            httponly=True,
            max_age=3600,
            secure=settings.cookie_secure,
            samesite=settings.cookie_samesite
        )
        redirect.set_cookie(
            key="refresh_token",
            value=response.session.refresh_token,
            httponly=True,
            max_age=7 * 24 * 3600,  # 7 days
            secure=settings.cookie_secure,
            samesite=settings.cookie_samesite
        )
        logger.debug("Auth cookies set, redirecting to home page")
        return redirect
    except HTTPException as e:
        logger.error(f"Login HTTP exception: {e.detail}")
        return templates.TemplateResponse(
            "login.html", 
            {"request": request, "error": e.detail}
        )
    except Exception as e:
        logger.error(f"Unexpected login error: {str(e)}")
        logger.exception("Login exception details:")
        return templates.TemplateResponse(
            "login.html", 
            {"request": request, "error": f"Login failed: {str(e)}"}
        ) 