"""
Base Extension Class

Base class for all PyServe extensions.
Defines a common interface and validation methods.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class BaseExtension(ABC):
    """
    Base class for all PyServe extensions.

    All extensions must inherit from this class and implement
    the validate() method to check the correctness of the configuration.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Extension initialization.
        Generic initialization method.

        Args:
            config: Extension configuration

        Raises:
            ValueError: If the configuration is invalid
        """
        self.config = config
        self.enabled = config.get('enabled', True)

        # Validate configuration
        validation_errors = self.validate()
        if validation_errors:
            raise ValueError(f"Extension validation failed: {', '.join(validation_errors)}")
    
    @abstractmethod
    def validate(self) -> List[str]:
        """
        Validate extension configuration.
        This method must be implemented by all extensions to check
        the correctness of its configuration.
        Returns:
            List of validation errors. An empty list indicates successful validation.
        """
        pass
    
    def is_enabled(self) -> bool:
        """Check if the extension is enabled."""
        return self.enabled
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """Get a value from the configuration."""
        return self.config.get(key, default)


class ExtensionLoadError(Exception):
    """Exception raised when an extension fails to load."""
    # TODO: add more specific load error handling
    pass


class ExtensionValidationError(Exception):
    """Exception raised when an extension fails validation."""
    # TODO: add more specific validation error handling
    pass
