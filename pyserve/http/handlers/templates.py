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
        try:
            return await self.template_engine.render_error(status_code, status_text, error_details)
        except Exception as e:
            return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{status_code} - {status_text}</title>
    <style>
        body {{ 
            font-family: Arial, sans-serif; 
            margin: 40px; 
            text-align: center; 
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        h1 {{ 
            color: #e74c3c; 
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        .error {{ 
            background: #ffe6e6; 
            padding: 20px; 
            border-radius: 4px; 
            margin: 20px 0; 
            border-left: 4px solid #e74c3c;
        }}
        a {{
            color: white;
            background: #3182ce;
            padding: 10px 20px;
            text-decoration: none;
            border-radius: 4px;
            display: inline-block;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{status_code} - {status_text}</h1>
        <p>{error_details}</p>
        <div class="error">
            <strong>Critical Template Error:</strong> {str(e)}<br>
            <small>This is the final fallback handler.</small>
        </div>
        <p><a href="/">Return to home page</a></p>
        <hr style="margin: 20px 0; border: none; height: 1px; background: #ddd;">
        <small>PyServe - Critical error handler</small>
    </div>
</body>
</html>"""
