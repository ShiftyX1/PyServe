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
        
    async def render_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """
        Load and render template file with context
        
        Args:
            template_name: Template filename
            context: Variables to substitute in template
            
        Returns:
            str: Rendered template
        """
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
            return await self.render_template("errors.html", context)
        except Exception as e:
            return f"Error rendering template: {str(e)}"
            
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
        try:
            return await self.render_template(f"error_{status_code}.html", context)
        except:
            return await self.render_template("errors.html", context)
            
    def clear_cache(self):
        self._cache.clear()