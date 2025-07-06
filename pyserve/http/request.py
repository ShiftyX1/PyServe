"""
HTTP Request parsing and representation
"""
from urllib.parse import parse_qs, urlparse
from typing import Dict, Union, List, Optional, Any
import asyncio
from pyserve.core.logging import get_logger

logger = get_logger()

class HTTPRequest:
    def __init__(self, raw_request: Optional[bytes] = None):
        self.method: str = ""
        self.path: str = ""
        self.version: str = ""
        self.headers: Dict[str, str] = {}
        self.body: bytes = b""
        self.query_params: Dict[str, list] = {}
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None
        
        if raw_request:
            self._parse_raw_request(raw_request)
            
    def _parse_raw_request(self, raw_request: bytes) -> None:
        """Parse raw HTTP request data"""
        try:
            parts = raw_request.split(b'\r\n\r\n', 1)
            headers_part = parts[0]
            self.body = parts[1] if len(parts) > 1 else b''
            
            lines = headers_part.split(b'\r\n')
            if not lines:
                return
                
            request_line = lines[0].decode('utf-8')
            try:
                method, path, version = request_line.split(' ')
                self.method = method
                self.version = version
                
                if '?' in path:
                    path, query = path.split('?', 1)
                    self.query_params = parse_qs(query)
                self.path = path
                
            except ValueError:
                logger.error(f"Invalid request line: {request_line}")
                return
                
            for line in lines[1:]:
                try:
                    name, value = line.decode('utf-8').split(': ', 1)
                    self.headers[name.lower()] = value
                except ValueError:
                    logger.error(f"Invalid header line: {line}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error parsing raw request: {e}")
        
    @classmethod
    async def parse(cls, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> 'HTTPRequest':
        """Parse HTTP request from stream"""
        request = cls()
        request.reader = reader
        request.writer = writer
        
        try:
            request_line = await reader.readline()
            if not request_line:
                return None
                
            try:
                method, path, version = request_line.decode().strip().split(" ")
            except ValueError:
                logger.error(f"Invalid request line: {request_line}")
                return None
                
            request.method = method
            request.version = version
            
            if "?" in path:
                path, query = path.split("?", 1)
                request.query_params = parse_qs(query)
            request.path = path
            
            while True:
                line = await reader.readline()
                if line == b'\r\n' or not line:
                    break
                    
                try:
                    name, value = line.decode().strip().split(": ", 1)
                    request.headers[name.lower()] = value
                except ValueError:
                    logger.error(f"Invalid header line: {line}")
                    continue
                    
            content_length = request.headers.get('content-length')
            if content_length:
                try:
                    length = int(content_length)
                    request.body = await reader.read(length)
                except ValueError:
                    logger.error(f"Invalid content length: {content_length}")
                    
            return request
            
        except Exception as e:
            logger.error(f"Error parsing request: {e}")
            return None
            
    def get_header(self, name: str, default: Any = None) -> str:
        """Get header value case-insensitively"""
        return self.headers.get(name.lower(), default)
        
    def get_query_param(self, name: str, default: Optional[str] = None) -> Optional[str]:
        values = self.query_params.get(name, [])
        return values[0] if values else default
        
    def get_query_params(self, name: str) -> List[str]:
        return self.query_params.get(name, [])
        
    def is_valid(self) -> bool:
        return bool(self.method and self.path)
        
    def is_websocket(self) -> bool:
        """Check if request is a WebSocket upgrade request"""
        return (
            self.get_header('upgrade', '').lower() == 'websocket' and
            self.get_header('connection', '').lower() == 'upgrade' and
            'sec-websocket-key' in self.headers and
            'sec-websocket-version' in self.headers
        )
        
    def __repr__(self) -> str:
        return f"HTTPRequest(method={self.method}, path={self.path})"