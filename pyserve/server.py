import socket
import os
import threading
from urllib.parse import parse_qs, urlparse
from .logging import PyServeLogger
from .template import TemplateEngine
from http import HTTPStatus
from .utils import get_redirections
class HTTPRequest:
    def __init__(self, raw_request):
        self.method = None
        self.path = None
        self.query_params = {}
        self.headers = {}
        self.body = b""
        self.parse_request(raw_request)

    def parse_request(self, raw_request):
        if not raw_request:
            return
            
        headers_part, *body_parts = raw_request.split(b'\r\n\r\n', 1)
        header_lines = headers_part.split(b'\r\n')
        
        if header_lines and header_lines[0]:
            request_line = header_lines[0].decode('utf-8')
            parts = request_line.split()
            if len(parts) >= 2:
                self.method = parts[0]
                url = parts[1]
                parsed_url = urlparse(url)
                self.path = parsed_url.path
                self.query_params = parse_qs(parsed_url.query)
        
        for i in range(1, len(header_lines)):
            line = header_lines[i].decode('utf-8')
            if ': ' in line:
                key, value = line.split(': ', 1)
                self.headers[key.lower()] = value
        
        if body_parts:
            self.body = body_parts[0]

class HTTPResponse:
    def __init__(self, status_code=200, headers=None, body=None):
        self.status_code = status_code
        self.headers = headers or {}
        self.body = body or b""
        
        if self.body and 'content-length' not in self.headers:
            self.headers['content-length'] = str(len(self.body))
        
        if 'content-type' not in self.headers:
            self.headers['content-type'] = 'text/html; charset=utf-8'

    def to_bytes(self):
        status_line = f"HTTP/1.1 {self.status_code} {HTTPStatus(self.status_code).phrase}\r\n"
        header_lines = ''.join(f"{k}: {v}\r\n" for k, v in self.headers.items())
        
        response = status_line.encode() + header_lines.encode() + b"\r\n"
        if self.body:
            response += self.body
            
        return response

class TCPServer:
    def __init__(self, host, port, backlog=5):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.host, self.port))
        self.socket.listen(backlog)
        self.logger = PyServeLogger()
        self.running = False

    def accept(self):
        return self.socket.accept()

    def close(self):
        self.logger.info("Shutting down server...")
        self.running = False
        self.socket.close()

    def run(self):
        self.running = True
        self.logger.info(f"Server started on {self.host}:{self.port}")
        
        while self.running:
            try:
                client_socket, client_address = self.accept()
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, client_address)
                )
                client_thread.daemon = True
                client_thread.start()
            except Exception as e:
                if self.running:  # Only log if not deliberately shutting down
                    self.logger.error(f"Error accepting connection: {e}")

    def handle_client(self, client_socket, client_address):
        self.logger.info(f"Connected to {client_address[0]}:{client_address[1]}")
        try:
            client_socket.settimeout(30)  # 30 second timeout
            request_data = client_socket.recv(4096)
            
            if not request_data:
                return
                
            response = self.handle_request(request_data, client_address)
            client_socket.sendall(response.to_bytes())
        except Exception as e:
            self.logger.error(f"Error handling client {client_address}: {e}")
        finally:
            client_socket.close()

    def handle_request(self, request_data, client_address):
        return HTTPResponse(
            status_code=200,
            body=b"TCP Server is running"
        )


class HTTPServer(TCPServer):
    def __init__(self, host, port, static_dir="./static", template_dir="./templates", backlog=5, debug=False, redirections: list = []):
        super().__init__(host, port, backlog)
        self.static_dir = os.path.abspath(static_dir)
        self.template_engine = TemplateEngine(template_dir)
        self.debug = debug
        self.redirections: dict = get_redirections(redirections)
        os.makedirs(self.static_dir, exist_ok=True)
        self.logger.info(f"Static files directory: {self.static_dir}")
        
        self.content_types = {
            '.html': 'text/html',
            '.css': 'text/css',
            '.js': 'application/javascript',
            '.json': 'application/json',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.svg': 'image/svg+xml',
            '.ico': 'image/x-icon',
        }

    def handle_request(self, request_data, client_address):
        request = HTTPRequest(request_data)
        
        if not request.method or not request.path:
            return HTTPResponse(400, body=b"Bad Request")
            
        self.logger.info(f"Received {request.method} request for {request.path} from {client_address[0]}:{client_address[1]}")

        if request.path in self.redirections:
            self.logger.info(f"Redirecting {request.path} to {self.redirections[request.path]}")
            return self.handle_redirection(request)
        elif request.path == '/':
            return self.handle_root(request)
        elif request.path.startswith('/static/'):
            return self.handle_static_file(request)
        else:
            file_path = os.path.join(self.static_dir, request.path.lstrip('/'))
            if os.path.isfile(file_path):
                return self.serve_static_file(file_path)
            else:
                return self.error_response(404, "Not Found", f"The requested URL {request.path} was not found on this server.")

    def handle_root(self, request):
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>PyServe - Welcome</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
                h1 { color: #2c3e50; }
                .container { max-width: 800px; margin: 0 auto; }
                .info { background-color: #f8f9fa; padding: 20px; border-radius: 5px; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Welcome to PyServe!</h1>
                <div class="info">
                    <p>Your HTTP server is running successfully.</p>
                    <p>You can place static files in the <code>static</code> directory.</p>
                </div>
            </div>
        </body>
        </html>
        """
        return HTTPResponse(200, body=html.encode())

    def handle_static_file(self, request):
        file_path = os.path.normpath(os.path.join(
            self.static_dir,
            request.path.replace('/static/', '', 1)
        ))
        
        if not file_path.startswith(self.static_dir):
            self.logger.warning(f"Attempted directory traversal: {request.path}")
            return self.error_response(403, "Forbidden", "You don't have permission to access this resource.")
            
        return self.serve_static_file(file_path)

    def serve_static_file(self, file_path):
        if not os.path.exists(file_path):
            self.logger.warning(f"File not found: {file_path}")
            return self.error_response(404, "Not Found", f"The requested file {os.path.basename(file_path)} was not found.")
            
        if not os.path.isfile(file_path):
            return self.error_response(403, "Forbidden", "You don't have permission to access this resource.")
        
        try:
            _, file_extension = os.path.splitext(file_path)
            content_type = self.content_types.get(file_extension.lower(), 'application/octet-stream')
            
            with open(file_path, 'rb') as file:
                content = file.read()
                
            headers = {
                'content-type': content_type,
                'content-length': str(len(content))
            }
            
            if self.debug:
                self.logger.debug(f"Serving static file: {file_path} ({content_type})")
            return HTTPResponse(200, headers=headers, body=content)
        except Exception as e:
            self.logger.error(f"Error serving {file_path}: {e}")
            return self.error_response(500, "Internal Server Error", "An unexpected error occurred while processing your request.")
        
    def error_response(self, status_code, status_text, error_details):
        error_template = self.template_engine.render_error(status_code, status_text, error_details)
        return HTTPResponse(status_code, body=error_template.encode())
    
    def reverse_proxy(self, request):
        pass
    
    def forward_proxy(self, request):
        pass

    def handle_redirection(self, request):
        return HTTPResponse(302, headers={'Location': self.redirections[request.path]})
