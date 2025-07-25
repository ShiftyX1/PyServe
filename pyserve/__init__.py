"""
PyServe - Async HTTP Server
Author: github.com/ShiftyX1 || Ilya Glazunov
"""
from .core.server import AsyncTCPServer, AsyncHTTPServer
from .http import HTTPRequest, HTTPResponse
from .core.logging import get_logger, PyServeLogger
from .template.engine import AsyncTemplateEngine
from .configuration import Configuration, SSLConfiguration
from .testing.config_tests import TestConfiguration

__version__ = '0.4.2'

__all__ = [
    'AsyncTCPServer',
    'AsyncHTTPServer',
    'HTTPRequest',
    'HTTPResponse',
    'PyServeLogger',
    'get_logger',
    'AsyncTemplateEngine',
    'Configuration',
    'TestConfiguration',
    'SSLConfiguration',
    '__version__'
]