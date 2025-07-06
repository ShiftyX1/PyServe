"""
Custom exceptions for configuration errors
"""

class ConfigurationError(Exception):
    """
    Base class for all configuration errors
    """
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

class PyServeYAMLException(ConfigurationError):
    """
    Exception raised for errors in YAML configuration
    """
    def __init__(self, message: str):
        super().__init__(message)