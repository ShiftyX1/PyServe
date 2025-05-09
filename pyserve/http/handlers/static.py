"""
Static file handler for PyServe
"""
import os
import aiofiles
from typing import Dict, Optional
from pyserve.http.request import HTTPRequest
from pyserve.http.response import HTTPResponse
from pyserve.core.logging import get_logger
from pyserve.utils.helpers import get_content_type


class StaticFileHandler:
    """Handles serving static files"""
    
    def __init__(self, static_dir: str, debug: bool = False):
        self.static_dir = os.path.abspath(static_dir)
        self.debug = debug
        self.logger = get_logger()
        
        self.content_types = {
            '.html': 'text/html',
            '.css': 'text/css',
            '.js': 'application/javascript',
            '.json': 'application/json',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.svg': 'image/svg+xml',
            '.ico': 'image/x-icon',
            '.woff': 'font/woff',
            '.woff2': 'font/woff2',
            '.ttf': 'font/ttf',
            '.otf': 'font/otf',
            '.pdf': 'application/pdf',
            '.txt': 'text/plain',
        }
        
    async def handle(self, request: HTTPRequest) -> HTTPResponse:
        file_path = os.path.normpath(os.path.join(
            self.static_dir,
            request.path.replace('/static/', '', 1)
        ))
        
        if not file_path.startswith(self.static_dir):
            self.logger.warning(f"Attempted directory traversal: {request.path}")
            return HTTPResponse(403, body="Forbidden: You don't have permission to access this resource.")
            
        return await self.serve_file(file_path)
        
    async def serve_file(self, file_path: str) -> HTTPResponse:
        """Serve a file from the filesystem"""
        if not os.path.exists(file_path):
            self.logger.warning(f"File not found: {file_path}")
            return HTTPResponse(404, body=f"Not Found: The requested file {os.path.basename(file_path)} was not found.")
            
        if not os.path.isfile(file_path):
            return HTTPResponse(403, body="Forbidden: You don't have permission to access this resource.")
        
        try:
            _, file_extension = os.path.splitext(file_path)
            content_type = self.content_types.get(file_extension.lower(), 'application/octet-stream')
            
            async with aiofiles.open(file_path, 'rb') as file:
                content = await file.read()
            
            headers = {
                'content-type': content_type,
                'content-length': str(len(content)),
                'cache-control': 'public, max-age=300'  # Cache for 5 minutes
            }
            
            if self.debug:
                self.logger.debug(f"Serving static file: {file_path} ({content_type})")
                
            return HTTPResponse(200, headers=headers, body=content)
            
        except Exception as e:
            self.logger.error(f"Error serving {file_path}: {e}")
            return HTTPResponse(500, body="Internal Server Error: An unexpected error occurred while processing your request.")
            
    def get_content_type(self, file_path: str) -> str:
        _, file_extension = os.path.splitext(file_path)
        return self.content_types.get(file_extension.lower(), 'application/octet-stream')