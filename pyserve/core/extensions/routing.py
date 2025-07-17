"""
Routing Extension

Extension for advanced routing with support for:
- Regex patterns (like in nginx)
- SPA fallback
- Route priorities
- Capturing parameters from URLs
"""

import re
from typing import Dict, Any, List, Optional, NamedTuple, Pattern
from .base import BaseExtension


class RouteMatch(NamedTuple):
    """Result of route matching."""
    pattern: str
    config: Dict[str, Any]
    params: Dict[str, str]
    priority: int


class RoutingExtension(BaseExtension):
    """
    Extension for regex routing and SPA support.

    Supports nginx-style priorities:
    1. Exact match (=/path)
    2. Regex match case-sensitive (~^/api/)
    3. Regex match case-insensitive (~*\\.(js|css)$)
    4. Prefix match (^~/static/)
    5. SPA fallback (__default__)
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        self.regex_locations = config.get('regex_locations', {})
        self.spa_config = None
        self.compiled_patterns: List[tuple] = []
        
        # Pattern compilation on initialization
        self._compile_patterns()
    
    def validate(self) -> List[str]:
        """Validate routing configuration."""
        errors = []
        
        regex_locations = self.config.get('regex_locations', {})
        if not isinstance(regex_locations, dict):
            errors.append("'regex_locations' must be a dictionary")
            return errors

        # Check each pattern
        for pattern, route_config in regex_locations.items():
            if not isinstance(route_config, dict):
                errors.append(f"Configuration for pattern '{pattern}' must be a dictionary")
                continue

            # Check special pattern __default__
            # need to ensure it has spa_fallback and root if specified
            if pattern == '__default__':
                if 'spa_fallback' in route_config and route_config['spa_fallback']:
                    if 'root' not in route_config:
                        errors.append("SPA fallback requires 'root' configuration")
                continue

            # Check regex patterns
            if pattern.startswith('~'):
                try:
                    flags = 0
                    pattern_str = pattern[1:]  # Remove ~

                    # Case-insensitive regex
                    if pattern.startswith('~*'):
                        flags = re.IGNORECASE
                        pattern_str = pattern[2:]  # Remove ~*
                    
                    re.compile(pattern_str, flags)
                except re.error as e:
                    errors.append(f"Invalid regex pattern '{pattern}': {e}")
            
            # proxy_pass check
            if 'proxy_pass' in route_config:
                proxy_pass = route_config['proxy_pass']
                if not isinstance(proxy_pass, str) or not proxy_pass.startswith('http'):
                    errors.append(f"Invalid proxy_pass '{proxy_pass}' for pattern '{pattern}'")
        
        return errors
    
    def _compile_patterns(self) -> None:
        """Compile and sort patterns by priority."""
        self.compiled_patterns = []
        
        for pattern, route_config in self.regex_locations.items():
            priority = self._get_pattern_priority(pattern)

            # Special handling for SPA fallback
            if pattern == '__default__':
                if route_config.get('spa_fallback', False):
                    self.spa_config = route_config
                self.compiled_patterns.append((pattern, None, route_config, priority))
                continue

            # Regex pattern compilation
            if pattern.startswith('~'):
                compiled_pattern = self._compile_regex_pattern(pattern)
                if compiled_pattern:
                    self.compiled_patterns.append((pattern, compiled_pattern, route_config, priority))
            else:
                # Regular patterns (prefix match)
                self.compiled_patterns.append((pattern, None, route_config, priority))

        # Sort by priority (lower = higher priority)
        self.compiled_patterns.sort(key=lambda x: x[3])
    
    def _compile_regex_pattern(self, pattern: str) -> Optional[Pattern]:
        """Compile regex pattern."""
        try:
            flags = 0
            pattern_str = pattern[1:]  # Remove ~

            # Case-insensitive regex
            if pattern.startswith('~*'):
                flags = re.IGNORECASE
                pattern_str = pattern[2:]  # Remove ~*

            return re.compile(pattern_str, flags)
        except re.error:
            return None
    
    def _get_pattern_priority(self, pattern: str) -> int:
        """
        Determine the priority of the pattern (nginx-style).
        Lower number = higher priority.
        """
        if pattern.startswith('='):
            return 1  # Exact match - highest priority
        elif pattern.startswith('~'):
            return 2  # Regex match
        elif pattern.startswith('^~'):
            return 3  # Prefix match (non-regex)
        elif pattern == '__default__':
            return 999  # SPA fallback - lowest priority
        else:
            return 4  # Regular prefix match

    def match_route(self, path: str) -> Optional[RouteMatch]:
        """
        Find the matching route for the given path.

        Args:
            path: Request path

        Returns:
            RouteMatch if a matching route is found, else None
        """
        for pattern, compiled_pattern, route_config, priority in self.compiled_patterns:
            # Check SPA fallback last
            if pattern == '__default__':
                continue
            
            params = {}
            match = False
            
            if compiled_pattern:
                # Regex match
                regex_match = compiled_pattern.search(path)
                if regex_match:
                    match = True
                    # Extract named groups
                    params = regex_match.groupdict()
            elif pattern.startswith('='):
                # Exact match
                exact_path = pattern[1:]
                match = (path == exact_path)
            elif pattern.startswith('^~'):
                # Prefix match (non-regex)
                prefix = pattern[2:]
                match = path.startswith(prefix)
            else:
                # Regular prefix match
                match = path.startswith(pattern)
            
            if match:
                return RouteMatch(
                    pattern=pattern,
                    config=route_config,
                    params=params,
                    priority=priority
                )

        # If nothing is found, check SPA fallback
        if self.spa_config and self.is_spa_route(path):
            return RouteMatch(
                pattern='__default__',
                config=self.spa_config,
                params={},
                priority=999
            )
        
        return None
    
    def is_spa_route(self, path: str) -> bool:
        """
        Check if the path is an SPA route.

        SPA routes:
        - Do not contain file extensions
        - Are not API paths
        - Are not static assets
        """
        if not self.spa_config:
            return False

        # Check for static files (with extensions)
        if '.' in path.split('/')[-1]:
            return False

        # Check for API paths (can be configured)
        api_patterns = self.spa_config.get('exclude_patterns', ['/api/', '/admin/'])
        for api_pattern in api_patterns:
            if path.startswith(api_pattern):
                return False
        
        return True
    
    def get_spa_config(self) -> Optional[Dict[str, Any]]:
        """Get SPA configuration."""
        return self.spa_config
    
    def get_compiled_patterns(self) -> List[tuple]:
        """Get compiled patterns (for debugging)."""
        return self.compiled_patterns.copy()
