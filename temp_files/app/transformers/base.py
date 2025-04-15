from typing import Dict, Any, Optional
from pydantic import HttpUrl
import logging
from urllib.parse import urlparse, unquote
import re
from app.models.ad_data import AdData

logger = logging.getLogger(__name__)

class DataTransformer:
    """Base class for transforming external data into AdData"""
    
    def extract_filename(self, url: str) -> Optional[str]:
        """Extract filename from URL"""
        if not url:
            return None
            
        # Common filename extraction logic
        parsed = urlparse(url)
        path = unquote(parsed.path)
        filename = path.split('/')[-1]
        
        if not filename or '.' not in filename:
            match = re.search(r'/([^/?]+\.[^/?]+)', url)
            if match:
                filename = match.group(1)
            else:
                return None
                
        return filename 