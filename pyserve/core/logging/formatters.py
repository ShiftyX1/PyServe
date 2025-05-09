"""
Log formatters for PyServe
"""
import logging

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
    
    def format(self, record) -> str:
        original_levelname = record.levelname
        
        levelname_color = self.LEVEL_COLORS.get(record.levelname, COLORS['RESET'])
        record.levelname = f"{levelname_color}{record.levelname}{COLORS['RESET']}"
        
        timestamp = self.formatTime(record, self.datefmt)
        record.server_info = f"{COLORS['BOLD']}[PyServe]{COLORS['RESET']} {COLORS['BLUE']}{timestamp}{COLORS['RESET']}"
        
        result = super().format(record)
        
        record.levelname = original_levelname
        
        return result


class StructuredFormatter(logging.Formatter):
    def format(self, record) -> str:
        import json
        
        log_entry = {
            'timestamp': self.formatTime(record, self.datefmt),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
            
        return json.dumps(log_entry)