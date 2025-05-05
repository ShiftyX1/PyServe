import os
import re
from typing import Dict, Any

class TemplateEngine:
    
    def __init__(self, templates_dir="./pyserve/templates"):
        self.templates_dir = os.path.abspath(templates_dir)
        os.makedirs(self.templates_dir, exist_ok=True)
        
    def render_string(self, template_string: str, context: Dict[str, Any]) -> str:
        for key, value in context.items():
            placeholder = r"{{" + key + r"}}"
            template_string = re.sub(placeholder, str(value), template_string)
            
        return template_string
        
    def render_template(self, template_name: str, context: Dict[str, Any]) -> str:
        template_path = os.path.join(self.templates_dir, template_name)
        
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                template_string = f.read()
            
            return self.render_string(template_string, context)
        except FileNotFoundError:
            return f"Template not found: {template_name}"
        except Exception as e:
            return f"Error rendering template: {str(e)}"
            
    def render_error(self, status_code: int, status_text: str, error_details: str = "") -> str:
        context = {
            "status_code": str(status_code),
            "status_text": status_text,
            "error_details": error_details
        }
        
        try:
            return self.render_template(f"error_{status_code}.html", context)
        except:
            return self.render_template("errors.html", context)