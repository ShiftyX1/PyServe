"""
WebSocket protocol implementation according to RFC 6455
"""
import struct
import base64
import hashlib
from typing import Tuple
from enum import IntEnum

class OpCode(IntEnum):
    CONTINUATION = 0x0
    TEXT = 0x1
    BINARY = 0x2
    CLOSE = 0x8
    PING = 0x9
    PONG = 0xA

class WebSocketFrame:
    def __init__(self, 
                 fin: bool = True,
                 opcode: OpCode = OpCode.TEXT,
                 payload: bytes = b'',
                 masked: bool = False):
        self.fin = fin
        self.opcode = opcode
        self.payload = payload
        self.masked = masked
        
    @classmethod
    def parse(cls, data: bytes) -> Tuple['WebSocketFrame', int]:
        """Parse WebSocket frame from bytes"""
        if len(data) < 2:
            return None, 0
            
        # First byte: FIN + RSV + Opcode
        byte1 = data[0]
        fin = bool(byte1 & 0x80)
        opcode = OpCode(byte1 & 0x0F)
        
        # Second byte: Mask + Payload length
        byte2 = data[1]
        masked = bool(byte2 & 0x80)
        payload_length = byte2 & 0x7F
        
        header_length = 2
        
        # Extended payload length
        if payload_length == 126:
            if len(data) < 4:
                return None, 0
            payload_length = struct.unpack('!H', data[2:4])[0]
            header_length = 4
        elif payload_length == 127:
            if len(data) < 10:
                return None, 0
            payload_length = struct.unpack('!Q', data[2:10])[0]
            header_length = 10
            
        # Masking key
        if masked:
            if len(data) < header_length + 4:
                return None, 0
            mask = data[header_length:header_length + 4]
            header_length += 4
            
        # Check if we have the full frame
        frame_length = header_length + payload_length
        if len(data) < frame_length:
            return None, 0
            
        payload = data[header_length:frame_length]
        
        # Unmask payload if needed
        if masked:
            payload = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
            
        frame = cls(fin=fin, opcode=opcode, payload=payload, masked=masked)
        return frame, frame_length
        
    def to_bytes(self) -> bytes:
        """Convert frame to bytes"""
        # First byte: FIN + RSV + Opcode
        byte1 = 0x80 if self.fin else 0  # FIN bit
        byte1 |= self.opcode
        
        # Second byte: Mask + Payload length
        byte2 = 0x80 if self.masked else 0  # MASK bit
        payload_length = len(self.payload)
        
        if payload_length <= 125:
            byte2 |= payload_length
            header = bytes([byte1, byte2])
        elif payload_length <= 65535:
            byte2 |= 126
            header = bytes([byte1, byte2]) + struct.pack('!H', payload_length)
        else:
            byte2 |= 127
            header = bytes([byte1, byte2]) + struct.pack('!Q', payload_length)
            
        # Add masking key and mask payload if needed
        if self.masked:
            import os
            mask = os.urandom(4)
            masked_payload = bytes(b ^ mask[i % 4] for i, b in enumerate(self.payload))
            return header + mask + masked_payload
            
        return header + self.payload

class WebSocket:
    GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
    
    @staticmethod
    def accept_key(key: str) -> str:
        """Generate WebSocket accept key"""
        sha1 = hashlib.sha1((key + WebSocket.GUID).encode()).digest()
        return base64.b64encode(sha1).decode()
        
    @staticmethod
    def is_websocket_request(headers: dict) -> bool:
        """Check if request is a WebSocket upgrade request"""
        return (
            headers.get('upgrade', '').lower() == 'websocket' and
            headers.get('connection', '').lower() == 'upgrade' and
            'sec-websocket-key' in headers and
            'sec-websocket-version' in headers
        )
        
    @staticmethod
    def create_accept_response(key: str) -> dict:
        """Create WebSocket accept response headers"""
        return {
            'Upgrade': 'websocket',
            'Connection': 'Upgrade',
            'Sec-WebSocket-Accept': WebSocket.accept_key(key)
        }
        
    @staticmethod
    def create_error_response() -> dict:
        """Create WebSocket error response headers"""
        return {
            'Connection': 'close'
        } 