"""
Configuration loader for PyServe
"""
import os
import yaml
from typing import Dict, Any


class ConfigLoader:
    @staticmethod
    def load_yaml(config_path: str) -> Dict[str, Any]:
        """
        Load configuration from YAML file
        
        Args:
            config_path: Path to YAML configuration file
            
        Returns:
            Dict[str, Any]: Configuration dictionary
        """
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f) or {}
        except FileNotFoundError:
            return {}
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML configuration: {e}")
        except Exception as e:
            raise RuntimeError(f"Error loading configuration: {e}")
    
    @staticmethod
    def save_yaml(config: Dict[str, Any], config_path: str) -> bool:
        """
        Save configuration to YAML file
        
        Args:
            config: Configuration dictionary
            config_path: Path to save configuration file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            config_dir = os.path.dirname(config_path)
            if config_dir and not os.path.exists(config_dir):
                os.makedirs(config_dir)
                
            with open(config_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False)
                
            return True
        except Exception as e:
            print(f"Error saving configuration: {e}")
            return False
    
    @staticmethod
    def create_default_config() -> Dict[str, Any]:
        """
        Create default configuration dictionary
        
        Returns:
            Dict[str, Any]: Default configuration
        """
        return {
            "server": {
                "host": "127.0.0.1",
                "port": 8000,
                "backlog": 5,
                "redirect_instructions": [
                    {"/home": "/index.html"},
                    {"/docs": "/docs.html"}
                ],
                "reverse_proxy": [
                    {
                        "path": "/api",
                        "host": "localhost",
                        "port": 3000
                    }
                ]
            },
            "http": {
                "static_dir": "./static",
                "templates_dir": "./templates"
            },
            "ssl": {
                "enabled": False,
                "cert_file": "./ssl/cert.pem",
                "key_file": "./ssl/key.pem" 
            },
            "logging": {
                "level": "INFO",
                "log_file": "./logs/pyserve.log",
                "console_output": True,
                "use_colors": True,
                "use_rotation": False,
                "max_log_size": 10485760,  # 10 MB
                "backup_count": 5,
                "structured_logs": False
            }
        }
    
    @staticmethod
    def load_environment_overrides(config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply environment variable overrides to configuration
        
        Args:
            config: Base configuration dictionary
            
        Returns:
            Dict[str, Any]: Configuration with environment overrides
        """
        env_overrides = {
            "PYSERVE_HOST": ("server", "host"),
            "PYSERVE_PORT": ("server", "port"),
            "PYSERVE_STATIC_DIR": ("http", "static_dir"),
            "PYSERVE_TEMPLATES_DIR": ("http", "templates_dir"),
            "PYSERVE_LOG_LEVEL": ("logging", "level"),
            "PYSERVE_LOG_FILE": ("logging", "log_file"),
            "PYSERVE_SSL_ENABLED": ("ssl", "enabled"),
            "PYSERVE_SSL_CERT": ("ssl", "cert_file"),
            "PYSERVE_SSL_KEY": ("ssl", "key_file"),
        }
        
        for env_var, (section, key) in env_overrides.items():
            if env_var in os.environ:
                value = os.environ[env_var]
                
                # Type conversion
                if key == "port":
                    value = int(value)
                elif key == "enabled":
                    value = value.lower() in ("true", "1", "yes", "on")
                    
                if section not in config:
                    config[section] = {}
                    
                config[section][key] = value
        
        return config