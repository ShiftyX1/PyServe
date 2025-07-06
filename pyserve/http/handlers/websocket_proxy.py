"""
WebSocket proxy handler implementation
"""
import asyncio
from typing import Dict, Any
from pyserve.http.websocket.base import WebSocketFrame, OpCode
from pyserve.core.logging import get_logger

logger = get_logger()

class WebSocketProxyHandler:
    def __init__(self, proxy_config: Dict[str, Any]):
        self.proxy_config = proxy_config
        self.host = proxy_config.get('host', 'localhost')
        self.port = proxy_config.get('port', 80)
        self.path = proxy_config.get('path', '/')
        self.ssl = proxy_config.get('ssl', False)
        
    async def handle_upgrade(self, client_reader: asyncio.StreamReader,
                           client_writer: asyncio.StreamWriter,
                           headers: Dict[str, str],
                           path: str) -> bool:
        """Handle WebSocket upgrade request"""
        try:
            backend_reader, backend_writer = await asyncio.open_connection(
                self.host, self.port, ssl=self.ssl
            )
            
            key = headers['sec-websocket-key']
            upgrade_request = (
                f"GET {path} HTTP/1.1\r\n"
                f"Host: {self.host}:{self.port}\r\n"
                f"Upgrade: websocket\r\n"
                f"Connection: Upgrade\r\n"
                f"Sec-WebSocket-Key: {key}\r\n"
                f"Sec-WebSocket-Version: {headers.get('sec-websocket-version', '13')}\r\n"
            )
            
            for name, value in headers.items():
                if name.lower() not in ['host', 'upgrade', 'connection', 
                                      'sec-websocket-key', 'sec-websocket-version']:
                    upgrade_request += f"{name}: {value}\r\n"
                    
            upgrade_request += "\r\n"
            
            backend_writer.write(upgrade_request.encode())
            await backend_writer.drain()
            
            response_line = await backend_reader.readline()
            if not response_line:
                return False
                
            status = response_line.decode().split()[1]
            if status != '101':
                logger.error(f"Backend WebSocket upgrade failed with status {status}")
                return False
                
            while True:
                line = await backend_reader.readline()
                if line == b'\r\n' or not line:
                    break
                client_writer.write(line)
                
            client_writer.write(b'\r\n')
            await client_writer.drain()
            
            await self._proxy_websocket(client_reader, client_writer,
                                      backend_reader, backend_writer)
            return True
            
        except Exception as e:
            logger.error(f"WebSocket proxy error: {e}")
            return False
            
    async def _proxy_websocket(self, 
                              client_reader: asyncio.StreamReader,
                              client_writer: asyncio.StreamWriter,
                              backend_reader: asyncio.StreamReader,
                              backend_writer: asyncio.StreamWriter):
        """Proxy WebSocket frames between client and backend"""
        try:
            client_to_backend = asyncio.create_task(
                self._forward_frames(client_reader, backend_writer, "client → backend")
            )
            backend_to_client = asyncio.create_task(
                self._forward_frames(backend_reader, client_writer, "backend → client")
            )
            
            done, pending = await asyncio.wait(
                [client_to_backend, backend_to_client],
                return_when=asyncio.FIRST_COMPLETED
            )
            
            for task in pending:
                task.cancel()
                
        except Exception as e:
            logger.error(f"WebSocket proxy error: {e}")
            
        finally:
            client_writer.close()
            backend_writer.close()
            await client_writer.wait_closed()
            await backend_writer.wait_closed()
            
    async def _forward_frames(self,
                            reader: asyncio.StreamReader,
                            writer: asyncio.StreamWriter,
                            direction: str):
        """Forward WebSocket frames from reader to writer"""
        buffer = bytearray()
        
        try:
            while True:
                data = await reader.read(8192)
                if not data:
                    break
                    
                buffer.extend(data)
                
                while buffer:
                    frame, length = WebSocketFrame.parse(buffer)
                    if not frame:
                        break
                        
                    buffer = buffer[length:]
                    
                    if frame.opcode not in [OpCode.PING, OpCode.PONG]:
                        logger.debug(
                            f"WebSocket {direction}: "
                            f"opcode={frame.opcode.name}, "
                            f"length={len(frame.payload)}"
                        )
                    
                    writer.write(frame.to_bytes())
                    await writer.drain()
                    
                    if frame.opcode == OpCode.CLOSE:
                        return
                        
        except Exception as e:
            logger.error(f"Error forwarding WebSocket frames: {e}")
            
        finally:
            writer.close()
            await writer.wait_closed()

