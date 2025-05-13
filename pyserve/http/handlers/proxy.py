"""
HTTP and WebSocket proxy handler implementation
"""
from typing import Dict, Any
from pyserve.http.request import HTTPRequest
from pyserve.http.response import HTTPResponse
from pyserve.http.websocket.base import WebSocket
from pyserve.http.handlers.websocket_proxy import WebSocketProxyHandler
from pyserve.core.logging import get_logger

logger = get_logger()

class ProxyHandler:
    def __init__(self, proxy_configs: list):
        self.proxy_configs = proxy_configs
        self.client_session = None
        
    def set_client_session(self, session):
        self.client_session = session
        
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
            return HTTPResponse(502, body="Bad Gateway")
            
        return None
        
    async def _handle_http(self, request: HTTPRequest, proxy_config: Dict[str, Any]) -> HTTPResponse:
        """Handle regular HTTP request"""
        if not self.client_session:
            return HTTPResponse(503, body="Service Unavailable")
            
        target_host = proxy_config.get('host', 'localhost')
        target_port = proxy_config.get('port', 80)
        use_ssl = proxy_config.get('ssl', False)
        
        scheme = 'https' if use_ssl else 'http'
        target_url = f"{scheme}://{target_host}:{target_port}{request.path}"
        
        try:
            async with self.client_session.request(
                method=request.method,
                url=target_url,
                headers=request.headers,
                data=request.body,
                allow_redirects=False
            ) as response:
                body = await response.read()
                
                return HTTPResponse(
                    status_code=response.status,
                    headers=dict(response.headers),
                    body=body
                )
                
        except Exception as e:
            logger.error(f"Proxy error: {e}")
            return HTTPResponse(502, body="Bad Gateway")