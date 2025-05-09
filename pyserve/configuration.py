"""
Configuration management for PyServe
"""
import os
import logging
from typing import Dict, Any, List, Optional, Union, Tuple
from pyserve.core.config.loader import ConfigLoader
from pyserve.core.config.validator import ConfigValidator


class SSLConfiguration:
    def __init__(self, config_dict: Optional[Dict[str, Any]] = None):
        config = config_dict or {}
        self.enabled = config.get('enabled', False)
        self.cert_file = config.get('cert_file', None)
        self.key_file = config.get('key_file', None)
        
    def is_properly_configured(self) -> bool:
        if not self.enabled:
            return False
            
        if not self.cert_file or not self.key_file:
            return False
            
        if not os.path.isfile(self.cert_file):
            return False
            
        if not os.path.isfile(self.key_file):
            return False
            
        return True
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            'enabled': self.enabled,
            'cert_file': self.cert_file,
            'key_file': self.key_file
        }


class Configuration:    
    def __init__(self, config_path: str = './config.yaml'):
        self.config_path = config_path
        self._config = self._load_configuration()
        
        self.server_config = self._config.get('server', {})
        self.http_config = self._config.get('http', {})
        self.logging_config = self._config.get('logging', {})
        self.ssl_config = SSLConfiguration(self._config.get('ssl', {}))
        self.redirections = self.server_config.get('redirect_instructions', [])
        self.locations = self.server_config.get('locations', [])
        
        if 'reverse_proxy' not in self.server_config:
            self.server_config['reverse_proxy'] = []
    
    def _load_configuration(self) -> Dict[str, Any]:
        config = ConfigLoader.load_yaml(self.config_path)
        
        if not config:
            config = ConfigLoader.create_default_config()
            ConfigLoader.save_yaml(config, self.config_path)
        
        config = ConfigLoader.load_environment_overrides(config)
        
        return config
    
    def validate(self) -> Tuple[bool, List[str]]:
        config_dict = {
            'server': self.server_config,
            'http': self.http_config,
            'logging': self.logging_config,
            'ssl': self.ssl_config.to_dict()
        }
        return ConfigValidator.validate_complete_config(config_dict)
    
    def get_log_level(self) -> int:
        level_str = self.logging_config.get('level', 'INFO').upper()
        levels = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        return levels.get(level_str, logging.INFO)
    
    def add_reverse_proxy(self, path: str, host: str, port: int) -> None:
        if 'reverse_proxy' not in self.server_config:
            self.server_config['reverse_proxy'] = []
            
        self.server_config['reverse_proxy'].append({
            'path': path,
            'host': host,
            'port': port
        })
        
        self._config['server'] = self.server_config
        self.save_config()
    
    def configure_ssl(self, enabled: bool, cert_file: Optional[str] = None, key_file: Optional[str] = None) -> None:
        self.ssl_config.enabled = enabled
        if cert_file:
            self.ssl_config.cert_file = cert_file
        if key_file:
            self.ssl_config.key_file = key_file
            
        self._config['ssl'] = self.ssl_config.to_dict()
        self.save_config()
    
    def save_config(self) -> bool:
        try:
            config = {
                'server': self.server_config,
                'http': self.http_config,
                'logging': self.logging_config,
                'ssl': self.ssl_config.to_dict()
            }
            
            return ConfigLoader.save_yaml(config, self.config_path)
        except Exception as e:
            print(f"Error saving configuration: {e}")
            return False
    
    def get(self, section: str, key: str, default: Any = None) -> Any:
        section_config = self._config.get(section, {})
        if isinstance(section_config, dict):
            return section_config.get(key, default)
        return default
    
    def set(self, section: str, key: str, value: Any) -> None:
        if section not in self._config:
            self._config[section] = {}
            
        self._config[section][key] = value
        
        if section == 'server':
            self.server_config = self._config['server']
        elif section == 'http':
            self.http_config = self._config['http']
        elif section == 'logging':
            self.logging_config = self._config['logging']
        elif section == 'ssl':
            self.ssl_config = SSLConfiguration(self._config['ssl'])
    
    def reload(self) -> None:
        self._config = self._load_configuration()
        
        self.server_config = self._config.get('server', {})
        self.http_config = self._config.get('http', {})
        self.logging_config = self._config.get('logging', {})
        self.ssl_config = SSLConfiguration(self._config.get('ssl', {}))
        self.redirections = self.server_config.get('redirect_instructions', [])
        
        if 'reverse_proxy' not in self.server_config:
            self.server_config['reverse_proxy'] = []
    
    def __str__(self) -> str:
        return f"Configuration(path={self.config_path})"
    
    def __repr__(self) -> str:
        return f"Configuration(path={self.config_path}, sections={list(self._config.keys())})"