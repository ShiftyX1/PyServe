"""
HTTP server implementation for PyServe
"""
import ssl
import os
from typing import Optional, Union, List, Dict, Any
import aiohttp

from pyserve.core.server.tcp import AsyncTCPServer
from pyserve.http.request import HTTPRequest
from pyserve.http.response import HTTPResponse
from pyserve.http.handlers.static import StaticFileHandler
from pyserve.http.handlers.redirect import RedirectHandler
from pyserve.http.handlers.templates import TemplateHandler
from pyserve.http.handlers.proxy import ProxyHandler
from pyserve.http.handlers.auth.base import HTTPAuthBase
from pyserve.template.engine import AsyncTemplateEngine
from pyserve.utils.helpers import get_redirections


class AsyncHTTPServer(AsyncTCPServer):
    """HTTP server implementation"""
    
    def __init__(self, 
                 host: str, 
                 port: int, 
                 static_dir: str = "./static", 
                 template_dir: str = "./templates", 
                 backlog: int = 5, 
                 debug: bool = False, 
                 redirections: Optional[List[Dict[str, str]]] = None, 
                 reverse_proxy: Optional[List[Dict[str, Union[str, int]]]] = None,
                 locations: Optional[Dict[str, Any]] = None,
                 ssl_cert: Optional[str] = None,
                 ssl_key: Optional[str] = None):
        
        # Initialize SSL context if certificates are provided
        ssl_context = None
        if ssl_cert and ssl_key:
            ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            try:
                ssl_context.load_cert_chain(ssl_cert, ssl_key)
            except Exception as e:
                raise ValueError(f"Error loading SSL certificates: {e}")
        
        super().__init__(host, port, backlog, ssl_context)
        
        # Initialize server attributes
        self.static_dir = os.path.abspath(static_dir)
        self.template_dir = template_dir
        self.template_engine = AsyncTemplateEngine(template_dir)
        self.debug = debug
        self.redirections = get_redirections(redirections or [])
        self.locations = locations or {}
        self.reverse_proxy = reverse_proxy or []
        self.client_session: Optional[aiohttp.ClientSession] = None
        self.ssl_enabled = ssl_context is not None
        
        # Ensure directories exist
        os.makedirs(self.static_dir, exist_ok=True)
        
        # Initialize handlers
        self.static_handler = StaticFileHandler(self.static_dir, debug=debug)
        self.redirect_handler = RedirectHandler(self.redirections)
        self.template_handler = TemplateHandler(self.template_engine)
        self.proxy_handler = ProxyHandler(self.reverse_proxy)
        self.auth_handler = HTTPAuthBase  
        
    async def start(self) -> None:
        """Start the HTTP server"""
        # Initialize aiohttp client session for proxy
        self.client_session = aiohttp.ClientSession()
        self.proxy_handler.set_client_session(self.client_session)
        
        # Start the server
        await super().start()
        
    async def stop(self) -> None:
        """Stop the HTTP server"""
        # Close client session
        if self.client_session:
            await self.client_session.close()
            
        # Stop the server
        await super().stop()
        
    async def handle_request(self, request_data: bytes, client_address: tuple) -> bytes:
        """Handle HTTP request and return response bytes"""
        request = HTTPRequest(request_data)
        
        # Validate request
        if not request.is_valid():
            response = HTTPResponse(400, body=b"Bad Request")
            return response.to_bytes()
            
        # Log request
        self.logger.info(f"[{request.method}] | {request.path} from {client_address[0]}:{client_address[1]}")
        self.logger.info(f"User-Agent: {request.get_header('user-agent', 'Unknown')}")
        
        try:
            # Route request to appropriate handler
            response = await self._route_request(request)
        except Exception as e:
            self.logger.error(f"Error handling request: {e}")
            response = HTTPResponse.internal_error()
            
        return response.to_bytes()
        
    async def _route_request(self, request: HTTPRequest) -> HTTPResponse:
        """Route request to the appropriate handler"""
        # Check for proxy paths first
        for proxy_config in self.reverse_proxy:
            proxy_path = proxy_config.get('path', '/')
            if request.path.startswith(proxy_path):
                self.logger.info(f"Proxying request {request.path} to {proxy_config['host']}:{proxy_config['port']}")
                return await self.proxy_handler.handle(request, proxy_config)
        
        # Check for redirects
        if request.path in self.redirections:
            self.logger.info(f"Redirecting {request.path} to {self.redirections[request.path]}")
            return self.redirect_handler.handle(request)
        
        # Check for location settings
        if request.path in self.locations.keys():
            auth_handler_temp = self.auth_handler(self.locations[request.path])
            if not auth_handler_temp.authenticate(request):
                return HTTPResponse(
                    status_code=401,
                    headers={
                        "WWW-Authenticate": "Basic realm=\"Restricted Area\"",
                        "Content-Type": "text/html"
                    },
                    body="<h1>401 Unauthorized</h1><p>Authentication is required to access this resource.</p>"
                )
            
        # Handle root path
        if request.path == '/':
            return await self._handle_root(request)
            
        # Handle static files with /static/ prefix
        if request.path.startswith('/static/'):
            return await self.static_handler.handle(request)
            
        # Try to serve file from static directory
        file_path = os.path.join(self.static_dir, request.path.lstrip('/'))
        if os.path.isfile(file_path):
            return await self.static_handler.serve_file(file_path)
            
        # File not found
        return await self._handle_error(404, "Not Found", f"The requested URL {request.path} was not found on this server.")
        
    async def _handle_root(self, request: HTTPRequest) -> HTTPResponse:
        """Handle the root path"""
        ssl_status = "✅ HTTPS connection (SSL/TLS enabled)" if self.ssl_enabled else "⚠️ HTTP connection (SSL/TLS disabled)"
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>PyServe - Welcome</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
                h1 {{ color: #2c3e50; }}
                .container {{ max-width: 800px; margin: 0 auto; }}
                .info {{ background-color: #f8f9fa; padding: 20px; border-radius: 5px; }}
                .ssl-enabled {{ color: green; }}
                .ssl-disabled {{ color: orange; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Welcome to PyServe!</h1>
                <div class="info">
                    <p>Your Async HTTP server is running successfully.</p>
                    <p class="{('ssl-enabled' if self.ssl_enabled else 'ssl-disabled')}">{ssl_status}</p>
                    <p>You can place static files in the <code>static</code> directory.</p>
                    <p>You can find more information about PyServe in the <a href="/docs">documentation</a>.</p>
                    <p>Or you can just visit <a href="https://github.com/ShiftyX1/PyServe">GitHub repository</a> to get more information.</p>
                    <p>And don't forget about home page in basic configuration. It's <a href="/home">here</a>.</p>
                </div>
            </div>
        </body>
        </html>
        """
        return HTTPResponse.ok(html)
        
    async def _handle_error(self, status_code: int, status_text: str, error_details: str) -> HTTPResponse:
        """Handle error response with template"""
        error_template = await self.template_handler.render_error(status_code, status_text, error_details)
        return HTTPResponse(status_code, body=error_template)