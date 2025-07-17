"""
PyServe Extensions System

PyServe configuration with extensible modules system.
Provides modularity and extensibility without breaking changes.
"""

from .base import BaseExtension
from .registry import ExtensionRegistry
from .routing import RoutingExtension

# Automatically register built-in extensions
ExtensionRegistry.register('routing', RoutingExtension)

__all__ = ['BaseExtension', 'ExtensionRegistry', 'RoutingExtension']
