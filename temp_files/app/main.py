# At the top of main.py, before any imports
import os
from dotenv import load_dotenv
import logging
import starlette.templating
from starlette.templating import _TemplateResponse

# Load environment variables first thing
env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
if os.path.exists(env_file):
    # Load environment variables from .env file
    load_dotenv(env_file)
else:
    # Fall back to default location
    load_dotenv()  # Try default location

from fastapi import FastAPI, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from app.config import get_settings, settings
from app.middleware.auth_middleware import AuthMiddleware
from app.middleware.supabase_middleware import SupabaseConnectionMiddleware
from app.services.auth_service import AuthService
from app.services.connection_service import connection_service
from app.routers import ads, connections, api_keys, webhooks, legal
from app.auth.router import router as auth_router
from fastapi.openapi.utils import get_openapi
import jwt
from fastapi.middleware.cors import CORSMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Pablo",
    description="Backend API for Pablo",
    version="0.1.0",
    docs_url=None,  # Disable /docs
    redoc_url=None,  # Disable /redoc
    openapi_url=None  # Disable OpenAPI schema
)
settings = get_settings()
logger.info(f"Starting application in {settings.ENV} environment")
logger.info(f"Using domain: {settings.domain}")
logger.info(f"Template directory: {os.path.abspath('templates')}")
logger.info(f"Templates available: {os.listdir('templates') if os.path.exists('templates') else 'Directory not found'}")
templates = Jinja2Templates(directory="templates")

# Add custom filter for truncating characters
def truncatechars(value, length):
    if value and len(value) > length:
        return value[:length]
    return value

# Register the filter with Jinja2
templates.env.filters["truncatechars"] = truncatechars

# Mount the static directory if it exists
static_dir = "static"
if os.path.exists(static_dir) and os.path.isdir(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
else:
    logger.warning(f"Static directory '{static_dir}' does not exist. Static files will not be served.")
    # Create an empty directory to prevent errors
    os.makedirs(static_dir, exist_ok=True)
    # Mount it anyway to avoid errors in templates that reference static files
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development, you can restrict this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add middleware for authentication and Supabase session management
app.add_middleware(AuthMiddleware)
app.add_middleware(SupabaseConnectionMiddleware)

# Initialize services
# Import Supabase with error handling
try:
    from app.auth.supabase_auth import supabase
except Exception as e:
    import logging
    logging.error(f"Failed to initialize Supabase client: {str(e)}")
    raise RuntimeError(f"Application startup failed: {str(e)}")
auth_service = AuthService(supabase)
# We're now using the singleton connection_service instance
# No need to initialize it here

# Make services available to routes
app.state.auth_service = auth_service
# Use the imported singleton
app.state.connection_service = connection_service

# Include routers with prefixes for better organization
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(connections.router, prefix="/connections", tags=["connections"])
app.include_router(ads.router, prefix="/ads", tags=["ads"])
app.include_router(api_keys.router, prefix="/api-keys", tags=["api-keys"])
app.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
app.include_router(legal.router, prefix="/legal", tags=["legal"])

@app.get("/")
async def home(request: Request):
    try:
        logger.info("Loading index.html template")
        return templates.TemplateResponse(
            "index.html", 
            {
                "request": request, 
                "settings": settings.dict()
            }
        )
    except Exception as e:
        logger.error(f"Error loading template: {str(e)}")
        return JSONResponse({"error": "Template error", "details": str(e)})

@app.get("/routes")
async def get_routes():
    """
    Returns a list of all available routes in the application.
    """
    routes = []
    
    for route in app.routes:
        path = getattr(route, "path", None)
        name = getattr(route, "name", None)
        methods = getattr(route, "methods", None)
        
        if path and methods:
            routes.append({
                "path": path,
                "name": name,
                "methods": list(methods)
            })
    
    # Sort routes by path for easier reading
    routes.sort(key=lambda x: x["path"])
    
    return {"routes": routes} 

@app.get("/sitemap", response_class=HTMLResponse)
async def sitemap(request: Request):
    """
    Displays a human-readable sitemap of all routes.
    """
    routes = []
    
    for route in app.routes:
        path = getattr(route, "path", None)
        methods = getattr(route, "methods", None)
        
        if path and methods:
            routes.append({
                "path": path,
                "methods": list(methods)
            })
    
    # Sort routes by path
    routes.sort(key=lambda x: x["path"])
    
    return templates.TemplateResponse(
        "sitemap.html",
        {
            "request": request,
            "routes": routes
        }
    ) 

# Add an exception handler for redirecting to login
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code == 401:
        logger.warning(f"401 Unauthorized: {exc.detail} - Path: {request.url.path}")
        # If this is an API request (based on path or Accept header), return JSON
        if request.url.path.startswith("/api") or "application/json" in request.headers.get("accept", ""):
            return JSONResponse(
                status_code=401,
                content={"detail": exc.detail}
            )
        # Otherwise redirect to login
        return RedirectResponse(url="/auth/login")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.middleware("http")
async def add_settings_to_templates(request: Request, call_next):
    """Add settings to all template responses"""
    response = await call_next(request)
    
    # Only modify template responses
    if isinstance(response, _TemplateResponse):
        # Add settings to the context if not already present
        if "settings" not in response.context:
            response.context["settings"] = settings.dict()
    
    return response 