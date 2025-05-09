"""
Base server classes for PyServe
"""
import asyncio
from abc import ABC, abstractmethod
from typing import Optional, Tuple, Any


class BaseServer(ABC):
    def __init__(self, host: str, port: int, backlog: int = 5):
        self.host = host
        self.port = port
        self.backlog = backlog
        self.server: Optional[asyncio.Server] = None
        self.running = False
        
    @abstractmethod
    async def start(self) -> None:
        pass
        
    @abstractmethod
    async def stop(self) -> None:
        pass
        
    @abstractmethod
    async def handle_connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        pass
        
    def is_running(self) -> bool:
        return self.running and self.server is not None
        
    def get_address(self) -> Tuple[str, int]:
        return self.host, self.port