"""
Redirect handler for PyServe
"""
from typing import Dict
from pyserve.http.request import HTTPRequest
from pyserve.http.response import HTTPResponse


class RedirectHandler:
    def __init__(self, redirections: Dict[str, str]):
        self.redirections = redirections
        
    def handle(self, request: HTTPRequest) -> HTTPResponse:
        """
        Handle redirection request
        
        Args:
            request: HTTP request
            
        Returns:
            HTTPResponse: Redirect response
        """
        target_url = self.redirections.get(request.path)
        
        if not target_url:
            return HTTPResponse(404, body="Redirect target not found")
            
        if request.query_params:
            query_parts = []
            for key, values in request.query_params.items():
                for value in values:
                    query_parts.append(f"{key}={value}")
            if query_parts:
                target_url += "?" + "&".join(query_parts)
                
        return HTTPResponse.redirect(target_url, permanent=False)