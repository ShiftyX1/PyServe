import os
import re
from typing import Dict, Any
import aiofiles

class AsyncTemplateEngine:
    def __init__(self, templates_dir="./pyserve/templates"):
        self.templates_dir = os.path.abspath(templates_dir)
        os.makedirs(self.templates_dir, exist_ok=True)
        
    async def render_string(self, template_string: str, context: Dict[str, Any]) -> str:
        for key, value in context.items():
            placeholder = r"{{" + key + r"}}"
            template_string = re.sub(placeholder, str(value), template_string)
            
        return template_string
        
    async def render_template(self, template_name: str, context: Dict[str, Any]) -> str:
        template_path = os.path.join(self.templates_dir, template_name)    
        try:
            async with aiofiles.open(template_path, 'r', encoding='utf-8') as f:
                template_string = await f.read()
            
            return await self.render_string(template_string, context)
        except FileNotFoundError:
            return await self.render_template("errors.html", context)
        except Exception as e:
            return f"Error rendering template: {str(e)}"
            
    async def render_error(self, status_code: int, status_text: str, error_details: str = "") -> str:
        context = {
            "status_code": str(status_code),
            "status_text": status_text,
            "error_details": error_details
        }
        try:
            return await self.render_template(f"error_{status_code}.html", context)
        except:
            return await self.render_template("errors.html", context)
