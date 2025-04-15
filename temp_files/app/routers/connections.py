from fastapi import APIRouter, Request, HTTPException, Depends, Form, Query, Header
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from app.auth.notion_oauth import notion_oauth
from app.auth.airtable_oauth import airtable_oauth
from app.auth.supabase_auth import supabase
from app.auth.auth_utils import get_current_user
from app.middleware.auth_middleware import get_current_user_id
from app.services.notion_service import NotionService
import secrets
from app.auth.facebook_oauth import facebook_oauth
import logging
import jwt
from app.config import get_settings
import string
from datetime import datetime
import httpx
from app.services.connection_service import connection_service
from app.services.api_key_service import api_key_service, generate_api_key_for_user

router = APIRouter()
templates = Jinja2Templates(directory="templates")
logger = logging.getLogger(__name__)

settings = get_settings()

@router.get("/", response_class=HTMLResponse)
async def connections_page(request: Request, current_user = Depends(get_current_user)):
    # Log all cookies for debugging
    logger.debug(f"Request cookies: {request.cookies}")
    # Debug: Check if user is in request state
    logger.debug(f"User authenticated: {current_user.id}")
    
    # Get user's API key
    keys = await api_key_service.list_keys(current_user.id)
    logger.info(f"Retrieved API keys for user {current_user.id}: {keys}")

    if not keys:
        try:
            logger.info(f"No API keys found for user {current_user.id}, generating new key")
            await generate_api_key_for_user(current_user.id)
            logger.info(f"Generated API key for user {current_user.id} on connections page visit")
            # Refresh the keys after generation
            keys = await api_key_service.list_keys(current_user.id)
            logger.info(f"Refreshed keys after generation: {keys}")
        except Exception as e:
            logger.error(f"Failed to generate API key on connections page: {str(e)}")
            logger.exception(e)  # This will log the full stack trace

    # Get user connections
    user_id = current_user.id
    connections = connection_service.get_user_connections(user_id)
    logger.info(f"Retrieved connections data for user {user_id}")
    
    # Get the user's API key to display in the webhook URL
    api_key = None
    if keys:
        # Use the first key from the list (assuming we only need one)
        api_key = keys[0]['key']
        logger.info(f"Using API key (first 4 chars: {api_key[:4]}...)")
    else:
        logger.error("No API keys found in keys list")
    
    # Ensure connections has the right structure
    if not isinstance(connections, dict):
        connections = {'credentials': {}, 'api_key': api_key}
    elif 'credentials' not in connections:
        connections = {'credentials': connections, 'api_key': api_key}
    else:
        # Keep the existing structure but ensure API key is set
        connections['api_key'] = api_key
    
    # Fetch Notion databases if connected
    notion_credentials = connections.get('credentials', {}).get('notion', {})
    if notion_credentials and notion_credentials.get('access_token'):
        try:
            notion_service = NotionService(token=notion_credentials['access_token'])
            databases = notion_service.client.search(
                filter={
                    "property": "object",
                    "value": "database"
                }
            )
            
            # Extract relevant database information
            database_list = []
            for db in databases.get('results', []):
                database_list.append({
                    'id': db.get('id'),
                    'title': db.get('title', [{}])[0].get('plain_text', 'Untitled'),
                    'url': db.get('url'),
                    'icon': db.get('icon', {}).get('emoji') if db.get('icon', {}).get('type') == 'emoji' else db.get('icon', {}).get('external', {}).get('url')
                })
            notion_credentials['databases'] = database_list
            logger.info(f"Found {len(database_list)} Notion databases")
        except Exception as e:
            logger.error(f"Error fetching Notion databases: {str(e)}")
    
    # Fetch Airtable bases if connected
    airtable_credentials = connections.get('credentials', {}).get('airtable', {})
    if airtable_credentials and airtable_credentials.get('access_token'):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.airtable.com/v0/meta/bases",
                    headers={
                        "Authorization": f"Bearer {airtable_credentials['access_token']}",
                        "Content-Type": "application/json"
                    }
                )
                if response.status_code == 200:
                    bases_data = response.json()
                    base_list = []
                    # Default database icon SVG
                    default_icon = '''<svg class="w-4 h-4 text-gray-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
                    </svg>'''
                    for base in bases_data.get('bases', []):
                        base_list.append({
                            'id': base.get('id'),
                            'name': base.get('name'),
                            'url': f"https://airtable.com/{base.get('id')}",
                            'icon': base.get('icon', {}).get('url') or default_icon
                        })
                    airtable_credentials['bases'] = base_list
                    logger.info(f"Found {len(base_list)} Airtable bases")
                else:
                    logger.error(f"Error fetching Airtable bases: {response.text}")
        except Exception as e:
            logger.error(f"Error fetching Airtable bases: {str(e)}")
    
    # Final connections data structure
    logger.info(f"Final connections data structure ready (keys: {list(connections.keys()) if isinstance(connections, dict) else 'not a dict'})")
    logger.info(f"Connected services: {list(connections.get('credentials', {}).keys())}")
    
    # Create context with all variables for debugging
    context = {
        "request": request,
        "connections": connections,
        "api_key": api_key,
        "settings": settings,
        "is_authenticated": True,
        "current_user": current_user
    }
    logger.info(f"Template context keys: {context.keys()}")
    logger.info(f"API key in context: {'present' if api_key else 'missing'}")
    if api_key:
        logger.info(f"API key first 4 chars: {api_key[:4]}...")
    
    return templates.TemplateResponse(
        "connections.html",
        context
    )

@router.get("/notion/connect")
async def notion_connect(request: Request, current_user = Depends(get_current_user)):
    """Connect to Notion"""
    logger.info("Starting Notion OAuth flow")
    
    # Generate a random state for CSRF protection
    state = secrets.token_urlsafe(32)
    
    # Get the authorization URL
    auth_url = notion_oauth.get_auth_url(state)
    
    # Redirect to Notion's authorization page
    return RedirectResponse(url=auth_url)

@router.get("/notion/callback")
async def notion_callback(request: Request, code: str, state: str, current_user = Depends(get_current_user)):
    """Handle Notion OAuth callback"""
    logger.info("Received Notion OAuth callback")
    
    try:
        # Exchange the code for an access token
        token_data = await notion_oauth.get_access_token(code)
        
        # Store the token in your database
        await notion_oauth.store_token(current_user.id, token_data)
        
        # Redirect back to the connections page
        return RedirectResponse(url="/connections?message=Notion connected successfully", status_code=303)
    except Exception as e:
        logger.error(f"Error in Notion callback: {str(e)}")
        return RedirectResponse(url="/connections?error=Failed to connect to Notion", status_code=303)

@router.get("/notion/disconnect")
async def notion_disconnect(request: Request, current_user = Depends(get_current_user)):
    """Disconnect Notion integration"""
    logger.info("Notion disconnect route accessed")
    
    try:
        # Delete the credentials
        logger.info(f"Deleting Notion credentials for user {current_user.id}")
        result = supabase.table('service_credentials')\
            .delete()\
            .eq('user_id', current_user.id)\
            .eq('service_name', 'notion')\
            .execute()
        
        logger.info(f"Deletion result: {result}")
        
        return RedirectResponse(
            url="/connections?message=Notion disconnected successfully",
            status_code=303
        )
    except Exception as e:
        logger.error(f"Error disconnecting Notion: {str(e)}")
        return RedirectResponse(
            url="/connections?message=Error disconnecting Notion&error=true",
            status_code=303
        )

@router.get("/facebook/connect")
async def facebook_connect(request: Request, current_user = Depends(get_current_user)):
    """Connect to Facebook"""
    logger.info("Starting Facebook OAuth flow")
    
    # Generate a random state for CSRF protection
    state = secrets.token_urlsafe(32)
    
    # Get the authorization URL
    auth_url = facebook_oauth.get_auth_url(state)
    
    # Redirect to Facebook's authorization page
    return RedirectResponse(url=auth_url)

@router.get("/facebook/callback")
async def facebook_callback(request: Request, code: str, state: str = None, current_user = Depends(get_current_user)):
    """Handle Facebook OAuth callback"""
    logger.info(f"Received Facebook OAuth callback for user {current_user.id}")
    
    try:
        # Log the code length and state
        logger.info(f"Code length: {len(code)}, State: {state}")
        
        # Exchange the code for an access token
        logger.info("Attempting to get access token")
        token_data = await facebook_oauth.get_access_token(code)
        logger.info("Successfully got access token")
        
        # Store the token in your database
        logger.info(f"Attempting to store token for user {current_user.id}")
        await facebook_oauth.store_token(current_user.id, token_data)
        logger.info("Successfully stored token")
        
        # Verify the token works
        logger.info("Verifying token with Facebook API")
        user_info = await get_facebook_user_info(token_data["access_token"])
        logger.info(f"Token verified, Facebook user ID: {user_info.get('id')}")
        
        return RedirectResponse(url="/connections?message=Facebook connected successfully", status_code=303)
    except Exception as e:
        logger.error(f"Error in Facebook callback: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        import traceback
        logger.error(f"Stack trace: {traceback.format_exc()}")
        return RedirectResponse(url=f"/connections?error=Failed to connect to Facebook: {str(e)}", status_code=303)

@router.get("/facebook/disconnect")
async def facebook_disconnect(request: Request, current_user = Depends(get_current_user)):
    """Disconnect Facebook integration"""
    try:
        # Get the current access token
        credentials_response = supabase.table('service_credentials')\
            .select("access_token")\
            .eq('user_id', current_user.id)\
            .eq('service_name', 'facebook')\
            .execute()
        
        if credentials_response.data:
            access_token = credentials_response.data[0]['access_token']
            
            # Revoke the token on Facebook's side
            try:
                revoke_url = f"https://graph.facebook.com/v21.0/me/permissions"
                async with httpx.AsyncClient() as client:
                    await client.delete(
                        revoke_url,
                        params={"access_token": access_token}
                    )
                logger.info(f"Successfully revoked Facebook permissions for user {current_user.id}")
            except Exception as e:
                logger.error(f"Error revoking Facebook permissions: {str(e)}")
                # Continue with deletion even if revocation fails
        
        # Delete the credentials from your database
        supabase.table('service_credentials')\
            .delete()\
            .eq('user_id', current_user.id)\
            .eq('service_name', 'facebook')\
            .execute()
        
        return RedirectResponse(
            url="/connections/?message=Successfully disconnected Facebook&success=true",
            status_code=303
        )
    except Exception as e:
        logger.error(f"Error disconnecting Facebook: {str(e)}")
        return RedirectResponse(
            url="/connections/?message=Error disconnecting Facebook&error=true",
            status_code=303
        )

@router.get("/{service}/disconnect")
async def disconnect_service(service: str, current_user = Depends(get_current_user)):
    try:
        # Delete the service credentials
        supabase.table('service_credentials')\
            .delete()\
            .eq('user_id', current_user.id)\
            .eq('service_name', service)\
            .execute()
        
        return RedirectResponse(
            url=f"/connections?message={service.capitalize()} disconnected successfully",
            status_code=303
        )
    except Exception as e:
        return RedirectResponse(
            url=f"/connections?message=Error disconnecting {service}: {str(e)}&error=true",
            status_code=303
        )

@router.get("/simple-generate-api-key")
async def simple_generate_api_key(request: Request, current_user = Depends(get_current_user)):
    """Generate a simple API key for the user"""
    try:
        # This should be getting the current_user from the dependency
        user_id = current_user.id
        
        # Generate the key
        await generate_api_key_for_user(user_id)
        logger.info(f"Generated API key for user {user_id}")
        
        # Redirect back to the connections page
        return RedirectResponse(url="/connections/?message=API+key+generated+successfully", status_code=303)
    except Exception as e:
        logger.error(f"Error generating API key: {str(e)}")
        return templates.TemplateResponse(
            "connections.html", 
            {
                "request": request,
                "credentials": {},
                "api_key": None,
                "is_authenticated": True,
                "settings": settings,
                "current_user": current_user,
                "error_message": f"Error generating API key: {str(e)}"
            }
        )

@router.get("/airtable/connect")
async def airtable_connect(request: Request, current_user = Depends(get_current_user)):
    """Connect to Airtable"""
    try:
        logger.info("=== Starting Airtable OAuth flow ===")
        user_id = current_user.id
        logger.info(f"User authenticated: {user_id}")
        
        # Check if airtable_oauth is properly initialized
        if not hasattr(airtable_oauth, 'client_id') or not airtable_oauth.client_id:
            logger.error("Airtable OAuth client is not properly initialized")
            return RedirectResponse(url="/connections?message=Airtable OAuth is not properly configured&error=true", status_code=303)
        
        # Log detailed OAuth configuration
        logger.info(f"Airtable OAuth client_id: {airtable_oauth.client_id[:5] + '...' if airtable_oauth.client_id else 'None'}")
        logger.info(f"Airtable OAuth redirect_uri: {airtable_oauth.redirect_uri}")
        logger.info(f"Airtable OAuth client_secret exists: {bool(airtable_oauth.client_secret)}")
        
        # Generate a state parameter to prevent CSRF
        state = secrets.token_urlsafe(32)
        logger.info(f"Generated state: {state[:10]}...")
        
        # Log Airtable client ID and redirect URI
        logger.info(f"Settings from config - Airtable redirect URI: {settings.airtable_redirect_uri}")
        
        if not settings.airtable_client_id or not settings.airtable_client_secret:
            logger.error("Airtable OAuth credentials are missing")
            return RedirectResponse(url="/connections?message=Airtable OAuth credentials are not configured&error=true", status_code=303)
        
        # Generate the auth URL (this also generates and stores the code verifier)
        logger.info("Generating Airtable auth URL...")
        auth_url = airtable_oauth.get_auth_url(state)
        logger.info(f"Generated auth URL: {auth_url[:50]}...")
        code_verifier = airtable_oauth.code_verifier
        logger.info(f"Code verifier generated (length: {len(code_verifier)})")
        
        # Store state in session cookie instead of database
        response = RedirectResponse(url=auth_url)
        cookie_value = f"{state}:{user_id}:airtable:{code_verifier}"
        logger.info(f"Setting cookie 'oauth_state' with value format: state:user_id:airtable:code_verifier")
        logger.info(f"Cookie value length: {len(cookie_value)}")
        response.set_cookie(
            key="oauth_state",
            value=cookie_value,
            httponly=True,
            max_age=600  # 10 minutes
        )
        logger.info("Set state in cookie, redirecting to Airtable auth URL")
        
        return response
        
    except Exception as e:
        logger.exception(f"Error starting Airtable OAuth flow")
        return RedirectResponse(url="/connections?message=Error connecting to Airtable&error=true", status_code=303)

@router.get("/airtable/callback")
async def airtable_callback(request: Request, code: str = None, state: str = None, error: str = None, error_description: str = None):
    """Handle Airtable OAuth callback"""
    logger.info(f"Airtable callback received: code={code is not None}, state={state}, error={error}")
    logger.info(f"Request query params: {request.query_params}")
    logger.info(f"Request cookies: {request.cookies}")
    
    if error:
        error_msg = f"Airtable OAuth error: {error}"
        if error_description:
            error_msg += f" - {error_description}"
        logger.error(error_msg)
        return RedirectResponse(url=f"/connections?message=Error connecting to Airtable: {error_msg}&error=true", status_code=303)
    
    if not code or not state:
        return RedirectResponse(url="/connections?message=Invalid OAuth callback&error=true", status_code=303)
    
    try:
        # Get state from cookie
        cookie_state = request.cookies.get("oauth_state", "")
        if not cookie_state:
            return RedirectResponse(url="/connections?message=Invalid OAuth state (missing cookie)&error=true", status_code=303)
        
        # Parse cookie state
        parts = cookie_state.split(":", 3)  # Split into at most 4 parts
        if len(parts) != 4 or parts[0] != state or parts[2] != "airtable":
            return RedirectResponse(url="/connections?message=Invalid OAuth state (mismatch)&error=true", status_code=303)
        
        user_id = parts[1]
        code_verifier = parts[3]
        
        # Set the code verifier in the OAuth handler
        airtable_oauth.code_verifier = code_verifier
        
        # Exchange code for access token
        token_data = await airtable_oauth.get_access_token(code)
        
        # Store token in database
        await airtable_oauth.store_token(user_id, token_data)
        
        # Redirect to connections page with success message
        message = "Successfully connected to Airtable."
        response = RedirectResponse(url=f"/connections?message={message}", status_code=303)
        response.delete_cookie(key="oauth_state")
        return response
        
    except Exception as e:
        logger.error(f"Error in Airtable OAuth callback: {str(e)}")
        # Provide more specific error message
        error_message = str(e)
        if "generate_api_key" in error_message:
            error_message = "Error generating API key. Please try again."
        elif "token" in error_message.lower():
            error_message = "Error obtaining Airtable access token. Please try again."
        else:
            error_message = "Error connecting to Airtable. Please try again."
            
        return RedirectResponse(url=f"/connections?message={error_message}&error=true", status_code=303)

@router.get("/airtable/disconnect")
async def airtable_disconnect(request: Request, current_user = Depends(get_current_user)):
    """Disconnect Airtable"""
    try:
        user_id = current_user.id
        logger.info(f"Attempting to disconnect Airtable for user {user_id}")
        
        # First verify if credentials exist
        check = supabase.table('service_credentials')\
            .select("*")\
            .eq('user_id', user_id)\
            .eq('service_name', 'airtable')\
            .execute()
            
        if not check.data:
            logger.info(f"No Airtable credentials found for user {user_id}")
            return RedirectResponse(url="/connections?message=Already disconnected from Airtable", status_code=303)
            
        logger.info(f"Found Airtable credentials for user {user_id}: {check.data}")
        
        # Instead of deleting, update the record to null the tokens
        update_result = supabase.table('service_credentials')\
            .update({
                'access_token': None,
                'refresh_token': None,
                'updated_at': datetime.now().isoformat()
            })\
            .eq('user_id', user_id)\
            .eq('service_name', 'airtable')\
            .execute()
            
        logger.info(f"Update result: {update_result}")
        
        # Verify update
        verify = supabase.table('service_credentials')\
            .select("*")\
            .eq('user_id', user_id)\
            .eq('service_name', 'airtable')\
            .execute()
            
        if verify.data and verify.data[0].get('access_token'):
            logger.error(f"Failed to nullify Airtable credentials for user {user_id}")
            return RedirectResponse(
                url="/connections?message=Error: Failed to disconnect Airtable&error=true",
                status_code=303
            )
        
        return RedirectResponse(url="/connections?message=Successfully disconnected from Airtable", status_code=303)
        
    except Exception as e:
        error_message = f"Error disconnecting Airtable: {str(e)}"
        logger.error(error_message)
        return RedirectResponse(url=f"/connections?message={error_message}&error=true", status_code=303)

# Helper function to get user_id from token
async def get_user_id_from_token(request: Request):
    user_id = getattr(request.state, "user_id", None)
    
    # Try to decode token manually if no user_id in state
    if not user_id:
        token = request.cookies.get("access_token")
        if token:
            try:
                payload = jwt.decode(token, options={"verify_signature": False})
                user_id = payload.get("sub")
                request.state.user_id = user_id
            except Exception as e:
                logger.error(f"Error decoding token: {str(e)}")
    
    return user_id

# Add these helper functions
async def exchange_for_long_lived_token(short_lived_token, app_id, app_secret):
    """Exchange a short-lived token for a long-lived token"""
    try:
        settings = get_settings()
        exchange_url = f"https://graph.facebook.com/{settings.facebook_api_version}/oauth/access_token"
        params = {
            "grant_type": "fb_exchange_token",
            "client_id": app_id,
            "client_secret": app_secret,
            "fb_exchange_token": short_lived_token
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(exchange_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if "access_token" not in data:
                raise ValueError("No long-lived token in response")
                
            return data["access_token"]
    except Exception as e:
        logger.error(f"Error exchanging for long-lived token: {str(e)}")
        raise

async def get_facebook_user_info(access_token):
    """Get Facebook user info to verify the token"""
    try:
        user_info_url = "https://graph.facebook.com/me"
        params = {
            "access_token": access_token,
            "fields": "id,name,email"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(user_info_url, params=params)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error(f"Error getting Facebook user info: {str(e)}")
        raise

@router.get("/regenerate-api-key")
async def regenerate_api_key(request: Request, current_user = Depends(get_current_user)):
    """Regenerate the user's API key"""
    try:
        # Ensure we have a valid user
        if not current_user or not current_user.id:
            logger.error("Missing or invalid user in regenerate_api_key")
            return RedirectResponse(url="/auth/login?message=You+must+be+logged+in+to+regenerate+API+keys", status_code=302)
        
        # Delete existing keys
        keys = await api_key_service.list_keys(current_user.id)
        if keys:
            for key in keys:
                await api_key_service.delete_key(key['id'])
            logger.info(f"Deleted {len(keys)} existing API keys for user {current_user.id}")
        
        # Generate a new key
        await generate_api_key_for_user(current_user.id)
        logger.info(f"Regenerated API key for user {current_user.id}")
        
        return RedirectResponse(url="/connections?message=API key regenerated successfully", status_code=303)
    except Exception as e:
        logger.error(f"Failed to regenerate API key: {str(e)}")
        # Check if this is an authentication error
        if isinstance(e, HTTPException) and e.status_code == 401:
            return RedirectResponse(url="/auth/login?message=You+must+be+logged+in+to+regenerate+API+keys", status_code=302)
        return RedirectResponse(url="/connections?message=Failed to regenerate API key&error=true", status_code=303)

@router.get("/notion/validate")
async def validate_notion_token(
    request: Request,
    current_user = Depends(get_current_user),
    api_key: str = Query(None, description="Optional API key for testing customer connections")
):
    """Validate Notion token and list accessible databases"""
    try:
        # If API key is provided, get the user_id from it
        user_id = current_user.id
        if api_key:
            user_id, error_response = await api_key_service.validate_api_key(api_key)
            if error_response:
                return error_response
            logger.info(f"Using API key to validate Notion connection for user {user_id}")
        
        # Get user's Notion token from connections
        connections = connection_service.get_user_connections(user_id)
        notion_credentials = connections.get('credentials', {}).get('notion', {})
        token = notion_credentials.get('access_token')
        
        if not token:
            return JSONResponse(
                status_code=401,
                content={"error": "No Notion token found. Please connect to Notion first."}
            )
        
        # Initialize Notion client
        notion_service = NotionService(token=token)
        
        # Try to list databases to validate token
        try:
            databases = notion_service.client.search(
                filter={
                    "property": "object",
                    "value": "database"
                }
            )
            
            # Extract relevant database information
            database_list = []
            for db in databases.get('results', []):
                database_list.append({
                    'id': db.get('id'),
                    'title': db.get('title', [{}])[0].get('plain_text', 'Untitled'),
                    'url': db.get('url'),
                    'last_edited_time': db.get('last_edited_time')
                })
            
            return JSONResponse(
                status_code=200,
                content={
                    "valid": True,
                    "message": "Notion token is valid",
                    "databases": database_list,
                    "user_id": user_id  # Include user_id in response for verification
                }
            )
            
        except Exception as e:
            logger.error(f"Error validating Notion token: {str(e)}")
            return JSONResponse(
                status_code=401,
                content={
                    "valid": False,
                    "error": "Invalid Notion token. Please reconnect to Notion."
                }
            )
            
    except Exception as e:
        logger.error(f"Error in validate_notion_token: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error while validating Notion token"}
        ) 