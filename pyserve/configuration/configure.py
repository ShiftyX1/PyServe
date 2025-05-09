import os
import yaml
import logging

class SSLConfiguration:
    def __init__(self, config_dict=None):
        config = config_dict or {}
        self.enabled = config.get('enabled', False)
        self.cert_file = config.get('cert_file', None)
        self.key_file = config.get('key_file', None)
        
    def is_properly_configured(self):
        if not self.enabled:
            return False
            
        if not self.cert_file or not self.key_file:
            return False
            
        if not os.path.isfile(self.cert_file):
            return False
            
        if not os.path.isfile(self.key_file):
            return False
            
        return True
        
    def to_dict(self):
        return {
            'enabled': self.enabled,
            'cert_file': self.cert_file,
            'key_file': self.key_file
        }
        
class Configuration:
    def __init__(self, config_path='./config.yaml'):
        self.config_path = config_path
        config = self.load_config()
        
        self.server_config = config.get('server', {})
        
        self.http_config = config.get('http', {})
        
        self.logging_config = config.get('logging', {})
        
        self.ssl_config = SSLConfiguration(config.get('ssl', {}))

        self.redirections = self.server_config.get('redirect_instructions', [])
        
        if 'reverse_proxy' not in self.server_config:
            self.server_config['reverse_proxy'] = []

    def create_config(self):
        default_config = {
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
                "console_output": True
            }
        }
        
        config_dir = os.path.dirname(self.config_path)
        if config_dir and not os.path.exists(config_dir):
            os.makedirs(config_dir)
            
        with open(self.config_path, 'w') as f:
            yaml.dump(default_config, f, default_flow_style=False)
            
        return default_config

    def load_config(self):
        try:
            with open(self.config_path, 'r') as f:
                return yaml.load(f, Loader=yaml.SafeLoader) or {}
        except FileNotFoundError:
            return self.create_config()
        except Exception as e:
            print(f"Error loading configuration: {e}")
            return self.create_config()
            
    def get_log_level(self):
        level_str = self.logging_config.get('level', 'DEBUG').upper()
        levels = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        return levels.get(level_str, logging.DEBUG)
    
    def add_reverse_proxy(self, path, host, port):
        if 'reverse_proxy' not in self.server_config:
            self.server_config['reverse_proxy'] = []
            
        self.server_config['reverse_proxy'].append({
            'path': path,
            'host': host,
            'port': port
        })
        
        self.save_config()
        
    def configure_ssl(self, enabled, cert_file=None, key_file=None):
        self.ssl_config.enabled = enabled
        if cert_file:
            self.ssl_config.cert_file = cert_file
        if key_file:
            self.ssl_config.key_file = key_file
            
        self.save_config()
        
    def save_config(self):
        try:
            config = {
                'server': self.server_config,
                'http': self.http_config,
                'logging': self.logging_config,
                'ssl': self.ssl_config.to_dict()
            }
            
            with open(self.config_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False)
                
            return True
        except Exception as e:
            print(f"Error saving configuration: {e}")
            return False