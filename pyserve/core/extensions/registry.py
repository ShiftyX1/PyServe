"""
Extension Registry

PyServe extension registry. Manages the registration and instantiation of extensions.
"""

from typing import Dict, Type, Any
from .base import BaseExtension, ExtensionLoadError


class ExtensionRegistry:
    """
    PyServe extension registry class.
    """
    
    _registry: Dict[str, Type[BaseExtension]] = {}
    
    @classmethod
    def register(cls, ext_type: str, ext_class: Type[BaseExtension]) -> None:
        """
        Register a new extension type.
        This method allows users to register a new extension type with its class.
        Args:
            ext_type: Extension type (e.g., 'routing', 'security')
            ext_class: Extension class that inherits from BaseExtension
        """
        if not issubclass(ext_class, BaseExtension):
            raise ValueError(f"Extension class must inherit from BaseExtension")
        
        cls._registry[ext_type] = ext_class
    
    @classmethod
    def create(cls, ext_type: str, config: Dict[str, Any]) -> BaseExtension:
        """
        Create an instance of the extension.
        
        Args:
            ext_type: Extension type
            config: Extension configuration

        Returns:
            Instance of the extension

        Raises:
            ExtensionLoadError: If the extension type is not registered
        """
        if ext_type not in cls._registry:
            raise ExtensionLoadError(f"Unknown extension type: {ext_type}")
        
        try:
            extension_class = cls._registry[ext_type]
            return extension_class(config)
        except Exception as e:
            raise ExtensionLoadError(f"Failed to create extension '{ext_type}': {e}")
    
    @classmethod
    def get_registered_types(cls) -> list[str]:
        """Get a list of registered extension types."""
        return list(cls._registry.keys())
    
    @classmethod
    def is_registered(cls, ext_type: str) -> bool:
        """Check if an extension type is registered."""
        return ext_type in cls._registry
    
    @classmethod
    def clear_registry(cls) -> None:
        """Clear the registry (used in tests)."""
        cls._registry.clear()
