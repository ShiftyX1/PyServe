import os
import yaml
import logging

class Configuration:
    def __init__(self, config_path='./config.yaml'):
        self.config_path = config_path
        config = self.load_config()
        
        self.server_config = config.get('server', {})
        
        self.http_config = config.get('http', {})
        
        self.logging_config = config.get('logging', {})

        self.redirections = self.server_config.get('redirect_instructions', [])
        
        if 'reverse_proxy' not in self.server_config:
            self.server_config['reverse_proxy'] = []

    def create_config(self):
        """Creates default configuration file"""
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
        """Loads configuration from file"""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.load(f, Loader=yaml.SafeLoader) or {}
        except FileNotFoundError:
            return self.create_config()
        except Exception as e:
            print(f"Error loading configuration: {e}")
            return self.create_config()
            
    def get_log_level(self):
        """Gets logging level from configuration"""
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
        """Adds reverse proxy configuration"""
        if 'reverse_proxy' not in self.server_config:
            self.server_config['reverse_proxy'] = []
            
        self.server_config['reverse_proxy'].append({
            'path': path,
            'host': host,
            'port': port
        })
        
        self.save_config()
        
    def save_config(self):
        """Saves current configuration to file"""
        try:
            config = {
                'server': self.server_config,
                'http': self.http_config,
                'logging': self.logging_config
            }
            
            with open(self.config_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False)
                
            return True
        except Exception as e:
            print(f"Error saving configuration: {e}")
            return False
