import base64
from pyserve.http.request import HTTPRequest
from pyserve.http.response import HTTPResponse
from pyserve.core.logging import get_logger

logger = get_logger()

class HTTPBasicAuthHandler:
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password

    def authenticate(self, request: HTTPRequest) -> bool:
        auth_header = request.headers.get("authorization")
        
        if not auth_header:
            logger.debug("No Authorization header present")
            return False
            
        try:
            auth_type, auth_string = auth_header.split(' ', 1)
            
            if auth_type.lower() != 'basic':
                logger.warning(f"Unsupported authentication type: {auth_type}")
                return False
                
            decoded = base64.b64decode(auth_string).decode('utf-8')
            username, password = decoded.split(':', 1)
            
            if username == self.username and password == self.password:
                logger.debug(f"Basic auth successful for user: {username}")
                return True
                
            logger.warning(f"Invalid credentials for user: {username}")
            return False
            
        except Exception as e:
            logger.error(f"Error processing basic auth: {e}")
            return False
            
