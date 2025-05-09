from typing import Dict, Any, Optional
from pyserve.http.request import HTTPRequest
from pyserve.core.logging import get_logger
from pyserve.http.handlers.auth.basic import HTTPBasicAuthHandler
logger = get_logger()

class HTTPAuthBase:
    def __init__(self, location_settings: Dict[str, Any]):
        self.location_settings = location_settings
        
    def authenticate(self, request: HTTPRequest) -> bool:
        auth_type = self._get_auth_type(request)
        if not auth_type:
            return False
        
        if auth_type == "basic":
            return self._authenticate_basic(request)
        
    def _get_auth_type(self, request: HTTPRequest) -> Optional[str]:
        auth_settings = self.location_settings.get("auth", {})
        if not auth_settings:
            return None
        
        auth_type = auth_settings.get("type")
        if not auth_type:
            logger.warning(f"Auth settings for location {request.path} are missing type. Specify the type of authentication to use.")
            return None
        
        return auth_type
    
    def _authenticate_basic(self, request: HTTPRequest) -> bool:
        auth_username = self.location_settings.get("auth", {}).get("username")
        auth_password = self.location_settings.get("auth", {}).get("password")

        if not auth_username or not auth_password:
            logger.warning(f"Auth settings for location {request.path} are missing username or password.")
            return False
        
        basic_auth_handler = HTTPBasicAuthHandler(auth_username, auth_password)
        return basic_auth_handler.authenticate(request)
        
        
    
    
        