"""
HTTP Request parsing and representation
"""
from urllib.parse import parse_qs, urlparse
from typing import Dict, Union, List, Optional


class HTTPRequest:
    def __init__(self, raw_request: bytes):
        self.method: Optional[str] = None
        self.path: Optional[str] = None
        self.query_params: Dict[str, List[str]] = {}
        self.headers: Dict[str, str] = {}
        self.body: bytes = b""
        self.version: Optional[str] = None
        self._parse_request(raw_request)
        
    def _parse_request(self, raw_request: bytes) -> None:
        if not raw_request:
            return
            
        headers_part, *body_parts = raw_request.split(b'\r\n\r\n', 1)
        header_lines = headers_part.split(b'\r\n')
        
        if header_lines and header_lines[0]:
            request_line = header_lines[0].decode('utf-8')
            parts = request_line.split()
            if len(parts) >= 2:
                self.method = parts[0]
                url = parts[1]
                parsed_url = urlparse(url)
                self.path = parsed_url.path
                self.query_params = parse_qs(parsed_url.query)
                if len(parts) >= 3:
                    self.version = parts[2]
        
        for i in range(1, len(header_lines)):
            line = header_lines[i].decode('utf-8')
            if ': ' in line:
                key, value = line.split(': ', 1)
                self.headers[key.lower()] = value
        
        if body_parts:
            self.body = body_parts[0]
            
    def get_header(self, name: str, default: Optional[str] = None) -> Optional[str]:
        return self.headers.get(name.lower(), default)
        
    def get_query_param(self, name: str, default: Optional[str] = None) -> Optional[str]:
        values = self.query_params.get(name, [])
        return values[0] if values else default
        
    def get_query_params(self, name: str) -> List[str]:
        return self.query_params.get(name, [])
        
    def is_valid(self) -> bool:
        return self.method is not None and self.path is not None
        
    def __repr__(self) -> str:
        return f"HTTPRequest(method={self.method}, path={self.path})"