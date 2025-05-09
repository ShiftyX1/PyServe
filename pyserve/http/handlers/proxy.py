"""
Reverse proxy handler for PyServe
"""
import gzip
import io
from typing import Optional, List, Dict, Union
import aiohttp
from pyserve.http.request import HTTPRequest
from pyserve.http.response import HTTPResponse
from pyserve.core.logging import get_logger
import pyserve


class ProxyHandler:
    def __init__(self, proxy_configs: List[Dict[str, Union[str, int]]]):
        self.proxy_configs = proxy_configs
        self.client_session: Optional[aiohttp.ClientSession] = None
        self.logger = get_logger()
        
    def set_client_session(self, client_session: aiohttp.ClientSession):
        self.client_session = client_session
        
    async def handle(self, request: HTTPRequest, proxy_config: Dict[str, Union[str, int]]) -> HTTPResponse:
        """
        Handle request through reverse proxy using aiohttp
        
        Args:
            request: HTTP request from client
            proxy_config: Proxy server configuration (host, port, path)
            
        Returns:
            HTTPResponse: Response from proxy server
        """
        try:
            target_host = proxy_config['host']
            target_port = proxy_config['port']
            base_path = proxy_config['path']
            
            if request.path.startswith(str(base_path)):
                target_path = request.path[len(str(base_path)):]
                if not target_path:
                    target_path = '/'
            else:
                target_path = request.path
                
            query_string = ""
            if request.query_params:
                query_parts = []
                for key, values in request.query_params.items():
                    for value in values:
                        query_parts.append(f"{key}={value}")
                if query_parts:
                    query_string = "?" + "&".join(query_parts)
                    
            target_url = f"http://{target_host}:{target_port}{target_path}{query_string}"
                
            if self.logger.logger.isEnabledFor(20):  # DEBUG level
                self.logger.debug(f"Connecting to {target_url}")
                
            proxy_headers = self._prepare_proxy_headers(request, target_host, target_port)
            
            if self.logger.logger.isEnabledFor(20):  # DEBUG level
                self.logger.debug(f"Proxy request: {request.method} {target_url}")
                self.logger.debug(f"Proxy headers: {proxy_headers}")
            
            async with self.client_session.request(
                method=request.method,
                url=target_url,
                headers=proxy_headers,
                data=request.body,
                allow_redirects=False
            ) as resp:
                body = await resp.read()
                
                body = self._handle_content_encoding(resp.headers, body)
                
                response_headers = self._prepare_response_headers(resp.headers, body)
                        
                return HTTPResponse(resp.status, response_headers, body)
                
        except Exception as e:
            self.logger.error(f"Async reverse proxy error: {e}")
            return HTTPResponse(502, body=f"Bad Gateway: Error proxying to {proxy_config['host']}:{proxy_config['port']}")
            
    def _prepare_proxy_headers(self, 
                              request: HTTPRequest, 
                              target_host: str, 
                              target_port: int) -> Dict[str, str]:
        proxy_headers = {}
        
        # Copy headers from original request (excluding hop-by-hop headers)
        hop_by_hop_headers = {
            'connection', 'keep-alive', 'proxy-authenticate', 
            'proxy-authorization', 'te', 'trailers', 
            'transfer-encoding', 'upgrade'
        }
        
        for name, value in request.headers.items():
            if name.lower() not in hop_by_hop_headers:
                proxy_headers[name] = value
                
        # Set host header
        proxy_headers['host'] = f"{target_host}:{target_port}"
        
        # Add X-Forwarded headers
        client_ip = request.get_header('x-forwarded-for', '')
        if client_ip:
            proxy_headers['x-forwarded-for'] = client_ip
        else:
            proxy_headers['x-forwarded-for'] = request.get_header('remote_addr', '')
            
        proxy_headers['x-forwarded-host'] = request.get_header('host', '')
        proxy_headers['x-forwarded-proto'] = 'http'
        
        return proxy_headers
        
    def _handle_content_encoding(self, headers: Dict[str, str], body: bytes) -> bytes:
        """Handle content encoding (e.g., gzip decompression)"""
        content_encoding = headers.get('content-encoding', '').lower()
        
        if content_encoding == 'gzip':
            try:
                gzip_file = gzip.GzipFile(fileobj=io.BytesIO(body))
                body = gzip_file.read()
            except Exception as e:
                self.logger.error(f"Error decompressing gzip response: {e}")
                
        return body
        
    def _prepare_response_headers(self, 
                                 resp_headers: Dict[str, str], 
                                 body: bytes) -> Dict[str, str]:
        """Prepare headers for response to client"""
        response_headers = {}
        
        # Copy headers from proxy response (excluding hop-by-hop headers)
        hop_by_hop_headers = {
            'connection', 'keep-alive', 'proxy-authenticate', 
            'proxy-authorization', 'te', 'trailers', 
            'transfer-encoding'
        }
        
        for header, value in resp_headers.items():
            if header.lower() not in hop_by_hop_headers:
                response_headers[header.lower()] = value
        
        # Update content-length if we decompressed
        if 'content-encoding' in response_headers and response_headers['content-encoding'] == 'gzip':
            response_headers['content-length'] = str(len(body))
            del response_headers['content-encoding']
            
        # Add Via header
        via_header = f"1.1 PyServe/{pyserve.__version__} (Async Reverse Proxy)"
        response_headers['via'] = via_header
        
        return response_headers