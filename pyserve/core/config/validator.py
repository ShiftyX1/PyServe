"""
Configuration validator for PyServe
"""
import os
import asyncio
import aiohttp
from typing import Dict, Any, List, Tuple, Optional

class ReverseProxyValidator:
    """Validator for reverse proxy configurations"""
    
    @staticmethod
    async def validate_proxy_availability(proxy_configs: List[Dict[str, Any]], 
                                          timeout: float = 5.0) -> Tuple[bool, List[str]]:
        """
        Validate that all reverse proxy backends are available
        
        Args:
            proxy_configs: List of proxy configurations
            timeout: Connection timeout in seconds
            
        Returns:
            Tuple[bool, List[str]]: (all_available, list_of_errors)
        """
        errors = []
        all_available = True
        
        async with aiohttp.ClientSession() as session:
            for i, proxy_config in enumerate(proxy_configs):
                host = proxy_config.get('host', 'localhost')
                port = proxy_config.get('port', 80)
                path = proxy_config.get('path', '/')
                use_ssl = proxy_config.get('ssl', False)
                
                error = await ReverseProxyValidator.check_backend(
                    session, host, port, path, use_ssl, timeout, i
                )
                
                if error:
                    errors.append(error)
                    all_available = False
                    
        return all_available, errors
    
    @staticmethod
    async def check_backend(session: aiohttp.ClientSession,
                           host: str,
                           port: int,
                           path: str,
                           use_ssl: bool,
                           timeout: float,
                           index: int) -> Optional[str]:
        """
        Check if a specific backend is available
        
        Args:
            session: aiohttp session
            host: Backend host
            port: Backend port
            path: Proxy path configuration
            use_ssl: Whether to use SSL
            timeout: Connection timeout
            index: Configuration index
            
        Returns:
            Optional[str]: Error message if backend is not available, None otherwise
        """
        scheme = 'https' if use_ssl else 'http'
        url = f"{scheme}://{host}:{port}/"
        
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=timeout)) as response:
                return None
                
        except aiohttp.ClientConnectorError as e:
            return f"reverse_proxy[{index}] ({path} -> {host}:{port}): Connection failed - {str(e)}"
            
        except asyncio.TimeoutError:
            return f"reverse_proxy[{index}] ({path} -> {host}:{port}): Connection timeout after {timeout}s"
            
        except Exception as e:
            return f"reverse_proxy[{index}] ({path} -> {host}:{port}): Unexpected error - {str(e)}"

    @staticmethod
    def validate_proxy_config(proxy_configs: List[Dict[str, Any]]) -> List[str]:
        """
        Validate proxy configuration structure (synchronous)
        
        Args:
            proxy_configs: List of proxy configurations
            
        Returns:
            List[str]: List of configuration errors
        """
        errors = []
        
        if not isinstance(proxy_configs, list):
            errors.append("reverse_proxy must be a list")
            return errors
            
        for i, proxy in enumerate(proxy_configs):
            if not isinstance(proxy, dict):
                errors.append(f"reverse_proxy[{i}] must be a dictionary")
                continue
                
            if 'path' not in proxy:
                errors.append(f"reverse_proxy[{i}] missing required field: path")
            if 'host' not in proxy:
                errors.append(f"reverse_proxy[{i}] missing required field: host")
            if 'port' not in proxy:
                errors.append(f"reverse_proxy[{i}] missing required field: port")
            elif not isinstance(proxy['port'], int) or proxy['port'] < 1 or proxy['port'] > 65535:
                errors.append(f"reverse_proxy[{i}] invalid port: {proxy['port']}")
                
        return errors

class ConfigValidator:
    @staticmethod
    def validate_complete_config(config: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate complete configuration
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Tuple[bool, List[str]]: (is_valid, list_of_errors)
        """
        errors = []
        
        server_errors = ConfigValidator.validate_server_config(config.get('server', {}))
        errors.extend(server_errors)
        
        http_errors = ConfigValidator.validate_http_config(config.get('http', {}))
        errors.extend(http_errors)
        
        ssl_config = config.get('ssl', {})
        if ssl_config.get('enabled', False):
            ssl_errors = ConfigValidator.validate_ssl_config(ssl_config)
            errors.extend(ssl_errors)
            
        logging_errors = ConfigValidator.validate_logging_config(config.get('logging', {}))
        errors.extend(logging_errors)
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_server_config(config: Dict[str, Any]) -> List[str]:
        """
        Validate server configuration section
        
        Args:
            config: Server configuration dictionary
            
        Returns:
            List[str]: List of validation errors
        """
        errors = []
        
        if 'host' not in config:
            errors.append("Missing required field: server.host")
        
        if 'port' not in config:
            errors.append("Missing required field: server.port")
        else:
            port = config.get('port')
            if not isinstance(port, int) or port < 1 or port > 65535:
                errors.append(f"Invalid port number: {port}. Must be between 1 and 65535")
        
        backlog = config.get('backlog', 5)
        if not isinstance(backlog, int) or backlog < 1:
            errors.append(f"Invalid backlog value: {backlog}. Must be a positive integer")
        
        redirections = config.get('redirect_instructions', [])
        if not isinstance(redirections, list):
            errors.append("redirect_instructions must be a list")
        else:
            for i, item in enumerate(redirections):
                if not isinstance(item, dict):
                    errors.append(f"redirect_instructions[{i}] must be a dictionary")
                elif len(item) != 1:
                    errors.append(f"redirect_instructions[{i}] must have exactly one key-value pair")
        
        reverse_proxy = config.get('reverse_proxy', [])
        proxy_errors = ReverseProxyValidator.validate_proxy_config(reverse_proxy)
        errors.extend(proxy_errors)
        
        return errors
    
    @staticmethod
    def validate_http_config(config: Dict[str, Any]) -> List[str]:
        """
        Validate HTTP configuration section
        
        Args:
            config: HTTP configuration dictionary
            
        Returns:
            List[str]: List of validation errors
        """
        errors = []
        
        if 'static_dir' not in config:
            errors.append("Missing required field: http.static_dir")
        
        if 'templates_dir' not in config:
            errors.append("Missing required field: http.templates_dir")
        
        return errors
    
    @staticmethod
    def validate_ssl_config(config: Dict[str, Any]) -> List[str]:
        """
        Validate SSL configuration section
        
        Args:
            config: SSL configuration dictionary
            
        Returns:
            List[str]: List of validation errors
        """
        errors = []
        
        if 'enabled' not in config:
            errors.append("Missing required field: ssl.enabled")
        elif not isinstance(config['enabled'], bool):
            errors.append("ssl.enabled must be a boolean value")
        
        if config.get('enabled', False):
            if 'cert_file' not in config:
                errors.append("Missing required field: ssl.cert_file (required when SSL is enabled)")
            elif not os.path.isfile(config['cert_file']):
                errors.append(f"SSL certificate file not found: {config['cert_file']}")
            
            if 'key_file' not in config:
                errors.append("Missing required field: ssl.key_file (required when SSL is enabled)")
            elif not os.path.isfile(config['key_file']):
                errors.append(f"SSL key file not found: {config['key_file']}")
        
        return errors
    
    @staticmethod
    def validate_logging_config(config: Dict[str, Any]) -> List[str]:
        """
        Validate logging configuration section
        
        Args:
            config: Logging configuration dictionary
            
        Returns:
            List[str]: List of validation errors
        """
        errors = []
        
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        level = config.get('level', 'INFO')
        if level not in valid_levels:
            errors.append(f"Invalid log level: {level}. Must be one of: {', '.join(valid_levels)}")
        
        log_file = config.get('log_file')
        if log_file:
            log_dir = os.path.dirname(log_file)
            if log_dir and not os.path.exists(log_dir):
                try:
                    os.makedirs(log_dir, exist_ok=True)
                except Exception as e:
                    errors.append(f"Cannot create log directory: {log_dir} - {str(e)}")
        
        bool_fields = ['console_output', 'use_colors', 'use_rotation', 'structured_logs']
        for field in bool_fields:
            if field in config and not isinstance(config[field], bool):
                errors.append(f"logging.{field} must be a boolean value")
        
        if config.get('use_rotation', False):
            if 'max_log_size' in config and not isinstance(config['max_log_size'], int):
                errors.append("logging.max_log_size must be an integer")
            if 'backup_count' in config and not isinstance(config['backup_count'], int):
                errors.append("logging.backup_count must be an integer")
        
        return errors
    
    @staticmethod
    def validate_directories(config: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate that required directories exist or can be created
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Tuple[bool, List[str]]: (all_valid, list_of_warnings)
        """
        warnings = []
        all_valid = True
        
        static_dir = config.get('http', {}).get('static_dir', './static')
        if not os.path.exists(static_dir):
            try:
                os.makedirs(static_dir, exist_ok=True)
                warnings.append(f"Created static directory: {static_dir}")
            except Exception as e:
                warnings.append(f"Failed to create static directory: {e}")
                all_valid = False
        
        templates_dir = config.get('http', {}).get('templates_dir', './templates')
        if not os.path.exists(templates_dir):
            try:
                os.makedirs(templates_dir, exist_ok=True)
                warnings.append(f"Created templates directory: {templates_dir}")
            except Exception as e:
                warnings.append(f"Failed to create templates directory: {e}")
                all_valid = False
        
        return all_valid, warnings
