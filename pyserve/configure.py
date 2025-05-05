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

    def create_config(self):
        default_config = {
            "server": {
                "host": "127.0.0.1",
                "port": 8000,
                "backlog": 5
            },
            "http": {
                "static_dir": "./static",
                "templates_dir": "./templates"
            },
            "logging": {
                "level": "DEBUG",
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