"""
Log handlers for PyServe
"""
import logging
import logging.handlers as original_handlers
import sys
import os
from typing import Optional
from .formatters import ColoredFormatter, StructuredFormatter


class ConsoleHandler(logging.StreamHandler):
    """
    Console handler with colored output
    """
    
    def __init__(self, level=logging.DEBUG, use_colors: bool = True):
        super().__init__(sys.stdout)
        self.setLevel(level)
        
        if use_colors:
            console_format = "%(server_info)s [%(levelname)s] %(message)s"
            console_formatter = ColoredFormatter(console_format, datefmt='%Y-%m-%d %H:%M:%S')
        else:
            console_format = "[%(asctime)s] [%(levelname)s] %(message)s"
            console_formatter = logging.Formatter(console_format, datefmt='%Y-%m-%d %H:%M:%S')
            
        self.setFormatter(console_formatter)


class FileHandler(logging.FileHandler):
    """
    File handler for logging to files
    """
    
    def __init__(self, filename: str, level=logging.DEBUG, structured: bool = False):
        logs_dir = os.path.dirname(filename)
        if logs_dir and not os.path.exists(logs_dir):
            os.makedirs(logs_dir)
            
        super().__init__(filename)
        self.setLevel(level)
        
        if structured:
            file_formatter = StructuredFormatter()
        else:
            file_format = "[%(asctime)s] [%(levelname)s] %(message)s"
            file_formatter = logging.Formatter(file_format, datefmt='%Y-%m-%d %H:%M:%S')
            
        self.setFormatter(file_formatter)


class RotatingFileHandler(original_handlers.RotatingFileHandler):
    """
    Rotating file handler with backup count
    """
    
    def __init__(self, filename: str, 
                 max_bytes: int = 10485760,  # 10 MB
                 backup_count: int = 5,
                 level=logging.DEBUG, 
                 structured: bool = False):
        logs_dir = os.path.dirname(filename)
        if logs_dir and not os.path.exists(logs_dir):
            os.makedirs(logs_dir)
            
        super().__init__(filename, maxBytes=max_bytes, backupCount=backup_count)
        self.setLevel(level)
        
        if structured:
            file_formatter = StructuredFormatter()
        else:
            file_format = "[%(asctime)s] [%(levelname)s] %(message)s"
            file_formatter = logging.Formatter(file_format, datefmt='%Y-%m-%d %H:%M:%S')
            
        self.setFormatter(file_formatter)