"""
Logging module for PyServe
"""
import logging
from .logger import PyServeLogger
from .formatters import ColoredFormatter, StructuredFormatter
from .handlers import ConsoleHandler, FileHandler, RotatingFileHandler


def get_logger(level=logging.DEBUG, log_file=None, **kwargs) -> PyServeLogger:
    """
    Create a PyServe logger instance
    
    Args:
        level: Logging level
        log_file: Path to log file (optional)
        **kwargs: Additional arguments for PyServeLogger
        
    Returns:
        PyServeLogger: Configured logger instance
    """
    return PyServeLogger(level, log_file, **kwargs)


__all__ = [
    'PyServeLogger',
    'get_logger',
    'ColoredFormatter',
    'StructuredFormatter',
    'ConsoleHandler',
    'FileHandler',
    'RotatingFileHandler'
]