"""
Helper utilities for PyServe
"""
from typing import Dict, List, Any
import logging

def get_logger_levels(level: str) -> int:
    """
    Get logger level from string
    """
    return {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }[level]

def get_redirections(redirections: List[Dict[str, str]]) -> Dict[str, str]:
    """
    Convert list of redirection dictionaries to a single dictionary
    
    Args:
        redirections: List of redirection configurations
        
    Returns:
        Dict[str, str]: Dictionary mapping source paths to target URLs
    """
    redirects_dict = {}
    
    for redirect_item in redirections:
        for path, url in redirect_item.items():
            redirects_dict[path] = url
    
    return redirects_dict

def get_locations(locations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Convert list of location dictionaries to a single dictionary
    
    Args:
        locations: List of location configurations
    """
    locations_dict = {}
    
    for location_item in locations:
        for path, config in location_item.items():
            locations_dict[path] = config
    
    return locations_dict


def get_content_type(file_path: str) -> str:
    """
    Get content type based on file extension
    
    Args:
        file_path: Path to the file
        
    Returns:
        str: MIME content type
    """
    import os
    
    _, file_extension = os.path.splitext(file_path)
    content_types = {
        '.html': 'text/html',
        '.css': 'text/css',
        '.js': 'application/javascript',
        '.json': 'application/json',
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.gif': 'image/gif',
        '.svg': 'image/svg+xml',
        '.ico': 'image/x-icon',
        '.woff': 'font/woff',
        '.woff2': 'font/woff2',
        '.ttf': 'font/ttf',
        '.otf': 'font/otf',
        '.pdf': 'application/pdf',
        '.txt': 'text/plain',
    }
    
    return content_types.get(file_extension.lower(), 'application/octet-stream')