"""
Logger implementation for PyServe
"""
import logging
from typing import Optional
from .handlers import ConsoleHandler, FileHandler, RotatingFileHandler


class PyServeLogger:
    """
    Custom logger for PyServe with support for multiple handlers
    """
    
    def __init__(self, 
                 level=logging.DEBUG, 
                 log_file: Optional[str] = None,
                 console_output: bool = True,
                 use_colors: bool = True,
                 use_rotation: bool = False,
                 max_log_size: int = 10485760,  # 10 MB TODO: Make this configurable
                 backup_count: int = 5,
                 structured_logs: bool = False):
        self.logger = logging.getLogger('pyserve')
        self.logger.setLevel(level)
        
        # Remove existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # Add console handler if requested
        if console_output:
            console_handler = ConsoleHandler(level=level, use_colors=use_colors)
            self.logger.addHandler(console_handler)
        
        # Add file handler if log file is specified
        if log_file:
            if use_rotation:
                file_handler = RotatingFileHandler(
                    log_file, 
                    max_bytes=max_log_size,
                    backup_count=backup_count,
                    level=level,
                    structured=structured_logs
                )
            else:
                file_handler = FileHandler(
                    log_file, 
                    level=level, 
                    structured=structured_logs
                )
            self.logger.addHandler(file_handler)
    
    def debug(self, message: str):
        """Log debug message"""
        self.logger.debug(message)
    
    def info(self, message: str):
        """Log info message"""
        self.logger.info(message)
    
    def warning(self, message: str):
        """Log warning message"""
        self.logger.warning(message)
    
    def error(self, message: str):
        """Log error message"""
        self.logger.error(message)
    
    def critical(self, message: str):
        """Log critical message"""
        self.logger.critical(message)
        
    def exception(self, message: str):
        """Log exception with traceback"""
        self.logger.exception(message)
        
    def set_level(self, level):
        """Set logging level"""
        self.logger.setLevel(level)
        for handler in self.logger.handlers:
            handler.setLevel(level)