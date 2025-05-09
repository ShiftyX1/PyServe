"""
Template handler for PyServe
"""
from typing import Dict, Any
from pyserve.http.request import HTTPRequest
from pyserve.http.response import HTTPResponse
from pyserve.template.engine import AsyncTemplateEngine


class TemplateHandler:
    def __init__(self, template_engine: AsyncTemplateEngine):
        self.template_engine = template_engine
        
    async def render(self, template_name: str, context: Dict[str, Any]) -> HTTPResponse:
        """
        Render a template and return HTTP response
        
        Args:
            template_name: Name of the template file
            context: Template context variables
            
        Returns:
            HTTPResponse: Response with rendered template
        """
        try:
            html = await self.template_engine.render_template(template_name, context)
            return HTTPResponse.ok(html, content_type="text/html; charset=utf-8")
        except Exception as e:
            return HTTPResponse.internal_error(f"Template rendering error: {str(e)}")
            
    async def render_error(self, status_code: int, status_text: str, error_details: str = "") -> str:
        """
        Render error page
        
        Args:
            status_code: HTTP status code
            status_text: Status text
            error_details: Error details text
            
        Returns:
            str: Rendered error page HTML
        """
        context = {
            "status_code": str(status_code),
            "status_text": status_text,
            "error_details": error_details
        }
        
        try:
            return await self.template_engine.render_template(f"error_{status_code}.html", context)
        except:
            try:
                return await self.template_engine.render_template("errors.html", context)
            except:
                return f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>{status_code} - {status_text}</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; margin: 40px; text-align: center; }}
                        h1 {{ color: #e74c3c; }}
                    </style>
                </head>
                <body>
                    <h1>{status_code} - {status_text}</h1>
                    <p>{error_details}</p>
                    <p><a href="/">Return to home page</a></p>
                </body>
                </html>
                """
