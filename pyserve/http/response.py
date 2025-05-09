"""
HTTP Response creation and serialization
"""
from http import HTTPStatus
from typing import Dict, Union, Optional
import pyserve


class HTTPResponse:    
    def __init__(self, 
                 status_code: int = 200, 
                 headers: Optional[Dict[str, str]] = None, 
                 body: Union[bytes, str] = b""):
        self.status_code = status_code
        self.headers = headers or {}
        self.body = body if isinstance(body, bytes) else body.encode('utf-8')
        
        self._set_default_headers()
        
    def _set_default_headers(self) -> None:
        """Set default headers if not already set"""
        if self.body and 'content-length' not in self.headers:
            self.headers['content-length'] = str(len(self.body))
        
        if 'content-type' not in self.headers:
            self.headers['content-type'] = 'text/html; charset=utf-8'
            
        if 'server' not in self.headers:
            self.headers['server'] = f'PyServe/{pyserve.__version__} (Async)'
            
    def set_header(self, name: str, value: str) -> None:
        self.headers[name.lower()] = value
        
    def set_cookie(self, name: str, value: str, **kwargs) -> None:
        cookie = f"{name}={value}"
        
        if 'max_age' in kwargs:
            cookie += f"; Max-Age={kwargs['max_age']}"
        if 'domain' in kwargs:
            cookie += f"; Domain={kwargs['domain']}"
        if 'path' in kwargs:
            cookie += f"; Path={kwargs['path']}"
        if 'secure' in kwargs and kwargs['secure']:
            cookie += "; Secure"
        if 'httponly' in kwargs and kwargs['httponly']:
            cookie += "; HttpOnly"
            
        self.headers['set-cookie'] = cookie
        
    def to_bytes(self) -> bytes:
        status_phrase = HTTPStatus(self.status_code).phrase
        status_line = f"HTTP/1.1 {self.status_code} {status_phrase}\r\n"
        
        header_lines = ''.join(f"{k}: {v}\r\n" for k, v in self.headers.items())
        
        response = status_line.encode() + header_lines.encode() + b"\r\n"
        if self.body:
            response += self.body
            
        return response
        
    @classmethod
    def ok(cls, body: Union[bytes, str] = b"", content_type: str = "text/html") -> 'HTTPResponse':
        return cls(200, {'content-type': content_type}, body)
        
    @classmethod
    def not_found(cls, message: str = "Not Found") -> 'HTTPResponse':
        return cls(404, body=message)
    
    @classmethod
    def unauthorized(cls, message: str = "Unauthorized") -> 'HTTPResponse':
        return cls(401, body=message)
        
    @classmethod
    def internal_error(cls, message: str = "Internal Server Error") -> 'HTTPResponse':
        return cls(500, body=message)
        
    @classmethod
    def redirect(cls, location: str, permanent: bool = False) -> 'HTTPResponse':
        status_code = 301 if permanent else 302
        return cls(status_code, {'location': location})
        
    def __repr__(self) -> str:
        return f"HTTPResponse(status={self.status_code})"