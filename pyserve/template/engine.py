"""
Template engine for PyServe
"""
import os
import re
from typing import Dict, Any
import aiofiles


class AsyncTemplateEngine:    
    def __init__(self, templates_dir: str = "./pyserve/templates"):
        self.templates_dir = os.path.abspath(templates_dir)
        os.makedirs(self.templates_dir, exist_ok=True)
        self._cache: Dict[str, str] = {}
        
    async def render_string(self, template_string: str, context: Dict[str, Any]) -> str:
        for key, value in context.items():
            placeholder = r"{{" + key + r"}}"
            template_string = re.sub(placeholder, str(value), template_string)
            
        return template_string
        
    async def render_template(self, template_name: str, context: Dict[str, Any], _recursion_depth: int = 0) -> str:
        """
        Load and render template file with context
        
        Args:
            template_name: Template filename
            context: Variables to substitute in template
            _recursion_depth: Internal parameter to prevent infinite recursion
            
        Returns:
            str: Rendered template
        """
        if _recursion_depth > 2:
            return self._get_hardcoded_fallback_html(
                context.get("status_code", "500"),
                context.get("status_text", "Internal Server Error"),
                context.get("error_details", "Template system recursion error")
            )
            
        template_path = os.path.join(self.templates_dir, template_name)    
        try:
            if template_name in self._cache:
                template_string = self._cache[template_name]
            else:
                async with aiofiles.open(template_path, 'r', encoding='utf-8') as f:
                    template_string = await f.read()
                    self._cache[template_name] = template_string
            
            return await self.render_string(template_string, context)
        except FileNotFoundError:
            # Only try fallback if we haven't exceeded recursion limit
            if _recursion_depth < 1:
                return await self.render_template("errors.html", context, _recursion_depth + 1)
            else:
                return self._get_hardcoded_fallback_html(
                    context.get("status_code", "404"),
                    context.get("status_text", "Not Found"), 
                    context.get("error_details", "") + " (Template file not found)"
                )
        except Exception as e:
            return self._get_hardcoded_fallback_html(
                context.get("status_code", "500"),
                context.get("status_text", "Internal Server Error"),
                context.get("error_details", "") + f" (Template error: {str(e)})"
            )
            
    async def render_error(self, status_code: int, status_text: str, error_details: str = "") -> str:
        """
        Render error page template
        
        Args:
            status_code: HTTP status code
            status_text: Status text (e.g., "Not Found")
            error_details: Additional error details
            
        Returns:
            str: Rendered error page HTML
        """
        context = {
            "status_code": str(status_code),
            "status_text": status_text,
            "error_details": error_details
        }
        
        # Try specific error template first
        try:
            return await self.render_template(f"error_{status_code}.html", context, 0)
        except Exception:
            try:
                return await self.render_template("errors.html", context, 1)
            except Exception:
                return self._get_hardcoded_fallback_html(status_code, status_text, error_details)
    
    def _get_hardcoded_fallback_html(self, status_code, status_text: str, error_details: str) -> str:
        status_code_str = str(status_code)
        
        return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{status_code_str} - {status_text}</title>
    <style>
        body {{ 
            font-family: Arial, sans-serif; 
            margin: 40px; 
            text-align: center; 
            background-color: #f5f5f5; 
            color: #333;
        }}
        .container {{ 
            max-width: 600px; 
            margin: 0 auto; 
            background: white; 
            padding: 40px; 
            border-radius: 8px; 
            box-shadow: 0 2px 10px rgba(0,0,0,0.1); 
        }}
        h1 {{ 
            color: #e74c3c; 
            margin-bottom: 20px; 
            font-size: 3em;
        }}
        p {{ 
            color: #666; 
            line-height: 1.5; 
            margin-bottom: 20px;
        }}
        a {{ 
            color: #3182ce; 
            text-decoration: none; 
            background: #3182ce;
            color: white;
            padding: 10px 20px;
            border-radius: 4px;
            display: inline-block;
        }}
        a:hover {{ 
            background: #2c5aa0;
        }}
        .error-details {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 4px;
            margin: 20px 0;
            font-size: 14px;
            color: #666;
            border-left: 4px solid #e74c3c;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{status_code_str}</h1>
        <h2>{status_text}</h2>
        <p>{error_details}</p>
        <div class="error-details">
            <strong>Template system error</strong><br>
            This is a fallback page to prevent infinite recursion.
        </div>
        <p><a href="/">Return to home page</a></p>
        <hr style="margin: 30px 0; border: none; height: 1px; background: #ddd;">
        <small style="color: #999;">PyServe - Emergency fallback</small>
    </div>
</body>
</html>"""
            
    def clear_cache(self):
        self._cache.clear()