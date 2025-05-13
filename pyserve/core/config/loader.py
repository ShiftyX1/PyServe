"""
Configuration loader for PyServe with enhanced error reporting
"""
import os
import yaml
import sys
from typing import Dict, Any
from pyserve.core.exceptions import PyServeYAMLException

class ConfigLoader:
    @staticmethod
    def load_yaml(config_path: str) -> Dict[str, Any]:
        """
        Load configuration from YAML file with enhanced error reporting
        
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
            try:
                with open(config_path, 'r') as f:
                    file_content = f.readlines()
            except:
                file_content = []
            
            error_message = ConfigLoader._format_yaml_error(e, file_content, config_path)
            
            ConfigLoader._print_colored_error(error_message)
            
            raise PyServeYAMLException(error_message)
        except Exception as e:
            raise RuntimeError(f"Error loading configuration: {e}")
    
    @staticmethod
    def _format_yaml_error(error: yaml.YAMLError, file_content: list, file_path: str) -> str:
        """
        Format YAML error message with file context
        
        Args:
            error: YAML error object
            file_content: List of file lines
            file_path: Path to the configuration file
            
        Returns:
            str: Formatted error message
        """
        error_msg = f"Cannot start server or even test the configuration file.\nInvalid YAML configuration in '{file_path}':\n"
        
        error_str = str(error)
        
        line_number = None
        if hasattr(error, 'context_mark') and error.context_mark:
            line_number = error.context_mark.line + 1
        elif hasattr(error, 'problem_mark') and error.problem_mark:
            line_number = error.problem_mark.line + 1
        else:
            import re
            match = re.search(r'line (\d+)', error_str)
            if match:
                line_number = int(match.group(1))
        
        if line_number and file_content:
            error_msg += f"\nError on line {line_number}:\n"
            error_msg += "─" * 50 + "\n"
            
            start_line = max(0, line_number - 3)
            end_line = min(len(file_content), line_number + 2)
            
            for i in range(start_line, end_line):
                line_num = i + 1
                line = file_content[i].rstrip('\n')
                
                if line_num == line_number:
                    error_msg += f"❌ {line_num:4d} | {line}\n"
                    
                    if hasattr(error, 'problem_mark') and error.problem_mark:
                        col = error.problem_mark.column
                        error_msg += "      " + " " * col + "^" + " ← error here\n"
                else:
                    error_msg += f"   {line_num:4d} | {line}\n"
            
            error_msg += "─" * 50 + "\n"
        
        error_msg += f"\nError details: {error_str}\nMore information: https://github.com/ShiftyX1/PyServe/issues"
        
        return error_msg
    
    @staticmethod
    def _print_colored_error(error_msg: str) -> None:
        """
        Print error message with colors if terminal supports it
        
        Args:
            error_msg: Error message to print
        """
        if sys.stdout.isatty() and os.name != 'nt':
            RED = '\033[91m'
            YELLOW = '\033[93m'
            RESET = '\033[0m'
            BOLD = '\033[1m'
            
            lines = error_msg.split('\n')
            colored_lines = []
            
            for line in lines:
                if line.startswith('❌'):
                    colored_lines.append(f"{RED}{BOLD}{line}{RESET}")
                elif line.startswith('Cannot start server or even test the configuration file.'):
                    colored_lines.append(f"{RED}{BOLD}{line}{RESET}")
                elif line.startswith('Invalid YAML'):
                    colored_lines.append(f"{RED}{BOLD}{line}{RESET}")
                elif 'Error on line' in line:
                    colored_lines.append(f"{YELLOW}{line}{RESET}")
                elif '←' in line:
                    colored_lines.append(f"{RED}{line}{RESET}")
                else:
                    colored_lines.append(line)
            
            print('\n'.join(colored_lines), file=sys.stderr)
        else:
            print(error_msg, file=sys.stderr)
    
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
                
                if key == "port":
                    value = int(value)
                elif key == "enabled":
                    value = value.lower() in ("true", "1", "yes", "on")
                    
                if section not in config:
                    config[section] = {}
                    
                config[section][key] = value
        
        return config