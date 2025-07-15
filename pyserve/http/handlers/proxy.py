"""
HTTP and WebSocket proxy handler implementation
"""
from typing import Dict, Any, Optional
from pyserve.http.request import HTTPRequest
from pyserve.http.response import HTTPResponse
from pyserve.http.websocket.base import WebSocket
from pyserve.http.handlers.websocket_proxy import WebSocketProxyHandler
from pyserve.core.logging import configured_logger
import asyncio
import aiohttp

logger = configured_logger

class ProxyHandler:
    def __init__(self, proxy_configs: list):
        self.proxy_configs = proxy_configs
        self.client_session = None
        self.template_handler = None
        
    def set_client_session(self, session):
        self.client_session = session
        
    def set_template_handler(self, template_handler):
        self.template_handler = template_handler
        
    async def handle(self, request: HTTPRequest, proxy_config: Dict[str, Any]) -> HTTPResponse:
        """Handle HTTP or WebSocket request"""
        if WebSocket.is_websocket_request(request.headers):
            return await self._handle_websocket(request, proxy_config)
            
        return await self._handle_http(request, proxy_config)
        
    async def _handle_websocket(self, request: HTTPRequest, proxy_config: Dict[str, Any]) -> HTTPResponse:
        """Handle WebSocket upgrade request"""
        ws_handler = WebSocketProxyHandler(proxy_config)
        
        client_reader = request.reader
        client_writer = request.writer
        
        if not client_reader or not client_writer:
            logger.error("No client connection available for WebSocket upgrade")
            return HTTPResponse(400, body="Bad Request")
            
        success = await ws_handler.handle_upgrade(
            client_reader,
            client_writer,
            request.headers,
            request.path
        )
        
        if not success:
            return await self._handle_error(502, "Bad Gateway", "WebSocket proxy connection failed")
            
        return None
        
    async def _handle_http(self, request: HTTPRequest, proxy_config: Dict[str, Any]) -> HTTPResponse:
        """Handle regular HTTP request"""
        if not self.client_session:
            return await self._handle_error(503, "Service Unavailable", "Proxy service is not available")
            
        target_host = proxy_config.get('host', 'localhost')
        target_port = proxy_config.get('port', 80)
        target_path = proxy_config.get('path', '')
        use_ssl = proxy_config.get('ssl', False)
        
        scheme = 'https' if use_ssl else 'http'
        
        relative_path = request.path
        if target_path and request.path.startswith(target_path):
            relative_path = request.path[len(target_path):]
            if not relative_path:
                relative_path = '/'
            elif not relative_path.startswith('/'):
                relative_path = '/' + relative_path
        
        target_url = f"{scheme}://{target_host}:{target_port}{relative_path}"
        
        if request.query_params:
            query_parts = []
            for key, values in request.query_params.items():
                for value in values:
                    query_parts.append(f"{key}={value}")
            if query_parts:
                target_url += "?" + "&".join(query_parts)
        
        backend_headers = {}
        skip_headers = {'host', 'connection', 'upgrade', 'transfer-encoding', 'content-length'}
        
        for name, value in request.headers.items():
            if name.lower() not in skip_headers:
                backend_headers[name] = value
        
        client_ip = request.headers.get('x-forwarded-for', 'unknown')
        backend_headers['X-Forwarded-For'] = client_ip
        backend_headers['X-Forwarded-Host'] = request.headers.get('host', '')
        backend_headers['X-Forwarded-Proto'] = 'https' if use_ssl else 'http'
        backend_headers['X-Real-IP'] = client_ip
        
        if request.body and len(request.body) > 0:
            backend_headers['Content-Length'] = str(len(request.body))
        
        try:
            logger.info(f"Proxying {request.method} request to {target_url}")
            
            timeout = aiohttp.ClientTimeout(total=30, connect=10)
            
            async with self.client_session.request(
                method=request.method,
                url=target_url,
                headers=backend_headers,
                data=request.body if request.body else None,
                allow_redirects=False,
                timeout=timeout,
                auto_decompress=True
            ) as response:
                body = await response.read()
                
                response_headers = {}
                skip_response_headers = {
                    'connection', 
                    'transfer-encoding', 
                    'content-encoding',
                    'keep-alive',
                    'upgrade',
                    'proxy-connection',
                    'server'
                }
                
                for name, value in response.headers.items():
                    if name.lower() not in skip_response_headers:
                        original_value = value
                        # Handle headers that might contain absolute URLs pointing to backend
                        if name.lower() in ['location', 'content-location', 'uri']:
                            value = self._rewrite_location_header(value, target_host, target_port, target_path, scheme, request)
                            if value != original_value:
                                logger.debug(f"Rewrote {name} header: '{original_value}' -> '{value}'")
                        response_headers[name] = value
                
                response_headers['content-length'] = str(len(body))
                
                response_headers['Via'] = 'pyserve-proxy'
                
                from pyserve import __version__
                response_headers['server'] = f'PyServe/{__version__}'
                
                logger.info(f"Proxy response: {response.status} (size: {len(body)} bytes)")
                logger.debug(f"Response headers: {response_headers}")
                
                return HTTPResponse(
                    status_code=response.status,
                    headers=response_headers,
                    body=body
                )
                
        except aiohttp.ClientError as e:
            logger.error(f"Proxy client error: {e}")
            return await self._handle_error(502, "Bad Gateway", f"Could not connect to upstream server: {str(e)}")
        except asyncio.TimeoutError:
            logger.error("Proxy request timeout")
            return await self._handle_error(504, "Gateway Timeout", "Upstream server did not respond in time")
        except Exception as e:
            logger.error(f"Proxy error: {e}")
            import traceback
            traceback.print_exc()
            return await self._handle_error(502, "Bad Gateway", "An unexpected error occurred while processing the request")
    
    def _rewrite_location_header(self, location: str, target_host: str, target_port: int, 
                                target_path: str, scheme: str, request: HTTPRequest) -> str:
        """
        Rewrite Location header to prevent domain/protocol substitution.
        Converts absolute URLs from backend to relative URLs for the client.
        """
        if not location:
            return location
            
        # If it's already a relative URL, keep it as is
        if location.startswith('/'):
            # If we have a target_path configured, we need to add it back
            if target_path and target_path != '/':
                return target_path.rstrip('/') + location
            return location
            
        # Check if this is an absolute URL pointing to our backend
        # Handle both explicit port and default ports (80 for http, 443 for https)
        backend_base_url = f"{scheme}://{target_host}:{target_port}"
        backend_base_url_default_port = f"{scheme}://{target_host}"
        
        # Check for explicit port first
        if location.startswith(backend_base_url):
            relative_path = location[len(backend_base_url):]
        # Check for default port (when port is omitted in URL)
        elif ((scheme == 'http' and target_port == 80) or (scheme == 'https' and target_port == 443)) and location.startswith(backend_base_url_default_port):
            relative_path = location[len(backend_base_url_default_port):]
        else:
            # For external URLs (not pointing to our backend), keep them as-is
            return location
            
        # Ensure the path starts with /
        if not relative_path:
            relative_path = '/'
        elif not relative_path.startswith('/'):
            relative_path = '/' + relative_path
            
        # If we have a target_path configured, add it back to make the URL accessible through proxy
        if target_path and target_path != '/':
            return target_path.rstrip('/') + relative_path
        
        return relative_path

    async def _handle_error(self, status_code: int, status_text: str, error_details: str) -> HTTPResponse:
        if self.template_handler:
            error_template = await self.template_handler.render_error(status_code, status_text, error_details)
            return HTTPResponse(status_code, body=error_template)
        else:
            return HTTPResponse(status_code, body=f"{status_code} {status_text}: {error_details}")