import asyncio
import ssl
from typing import Optional
from pyserve.core.logging import get_logger
from pyserve.core.server.base import BaseServer


class AsyncTCPServer(BaseServer):
    def __init__(self, host: str, port: int, backlog: int = 5, ssl_context: Optional[ssl.SSLContext] = None):
        super().__init__(host, port, backlog)
        self.ssl_context = ssl_context
        self.logger = get_logger()
        
    async def start(self) -> None:
        self.server = await asyncio.start_server(
            self.handle_connection,
            self.host,
            self.port,
            backlog=self.backlog,
            ssl=self.ssl_context
        )
        self.running = True
        
        protocol = "https" if self.ssl_context else "http"
        self.logger.info(f"TCP Server started on {protocol}://{self.host}:{self.port}")
        
        async with self.server:
            await self.server.serve_forever()
            
    async def stop(self) -> None:
        self.logger.info("Shutting down TCP server...")
        self.running = False
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            
    async def handle_connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        client_addr = writer.get_extra_info('peername')
        self.logger.info(f"Client connected from {client_addr[0]}:{client_addr[1]}")
        
        try:
            request_data = await asyncio.wait_for(reader.read(4096), timeout=30)
            
            if not request_data:
                return
                
            response = await self.handle_request(request_data, client_addr)
            writer.write(response)
            await writer.drain()
        except asyncio.TimeoutError:
            self.logger.warning(f"Timeout reading from client {client_addr}")
        except Exception as e:
            self.logger.error(f"Error handling client {client_addr}: {e}")
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except (ConnectionResetError, TimeoutError, ssl.SSLError):
                pass
                
    async def handle_request(self, request_data: bytes, client_address: tuple) -> bytes:
        """
        Handle request and return response
        This is meant to be overridden by subclasses
        """
        return b"HTTP/1.1 200 OK\r\n\r\nAsyncTCPServer is running"