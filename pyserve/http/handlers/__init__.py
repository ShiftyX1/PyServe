"""
HTTP handlers module for PyServe
"""
from .static import StaticFileHandler
from .redirect import RedirectHandler
from .templates import TemplateHandler
from .proxy import ProxyHandler

__all__ = [
    'StaticFileHandler',
    'RedirectHandler',
    'TemplateHandler',
    'ProxyHandler'
]