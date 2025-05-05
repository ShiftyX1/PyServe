import logging
import sys
import os
import time
from datetime import datetime

COLORS = {
    'RESET': '\033[0m',
    'BLACK': '\033[30m',
    'RED': '\033[31m',
    'GREEN': '\033[32m',
    'YELLOW': '\033[33m',
    'BLUE': '\033[34m',
    'MAGENTA': '\033[35m',
    'CYAN': '\033[36m',
    'WHITE': '\033[37m',
    'BOLD': '\033[1m',
    'UNDERLINE': '\033[4m',
    'BLINK': '\033[5m',
    'REVERSE': '\033[7m',
    'HIDDEN': '\033[8m',
    'BG_BLACK': '\033[40m',
    'BG_RED': '\033[41m',
    'BG_GREEN': '\033[42m',
    'BG_YELLOW': '\033[43m',
    'BG_BLUE': '\033[44m',
    'BG_MAGENTA': '\033[45m',
    'BG_CYAN': '\033[46m',
    'BG_WHITE': '\033[47m',
}

class ColoredFormatter(logging.Formatter):
    
    LEVEL_COLORS = {
        'DEBUG': COLORS['CYAN'],
        'INFO': COLORS['GREEN'],
        'WARNING': COLORS['YELLOW'],
        'ERROR': COLORS['RED'],
        'CRITICAL': COLORS['RED'] + COLORS['BOLD'],
    }
    
    def __init__(self, fmt=None, datefmt=None, style='%'):
        super().__init__(fmt, datefmt, style)
    
    def format(self, record):
        original_levelname = record.levelname
        
        levelname_color = self.LEVEL_COLORS.get(record.levelname, COLORS['RESET'])
        record.levelname = f"{levelname_color}{record.levelname}{COLORS['RESET']}"
        
        timestamp = self.formatTime(record, self.datefmt)
        record.server_info = f"{COLORS['BOLD']}[PyServe]{COLORS['RESET']} {COLORS['BLUE']}{timestamp}{COLORS['RESET']}"
        
        result = super().format(record)
        
        record.levelname = original_levelname
        
        return result

class PyServeLogger:
    def __init__(self, level=logging.DEBUG, log_file=None):
        self.logger = logging.getLogger('pyserve')
        self.logger.setLevel(level)
        
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_format = "%(server_info)s [%(levelname)s] %(message)s"
        console_formatter = ColoredFormatter(console_format, datefmt='%Y-%m-%d %H:%M:%S')
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        if log_file:
            logs_dir = os.path.dirname(log_file)
            if logs_dir and not os.path.exists(logs_dir):
                os.makedirs(logs_dir)
                
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(level)
            file_format = "[%(asctime)s] [%(levelname)s] %(message)s"
            file_formatter = logging.Formatter(file_format, datefmt='%Y-%m-%d %H:%M:%S')
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)
    
    def debug(self, message):
        self.logger.debug(message)
    
    def info(self, message):
        self.logger.info(message)
    
    def warning(self, message):
        self.logger.warning(message)
    
    def error(self, message):
        self.logger.error(message)
    
    def critical(self, message):
        self.logger.critical(message)

def get_logger(level=logging.DEBUG, log_file=None):
    return PyServeLogger(level, log_file)