import asyncio
import os
from urllib.parse import parse_qs, urlparse
from http import HTTPStatus
import io
import gzip
import aiofiles
import aiohttp
from .logging import PyServeLogger
from .template import AsyncTemplateEngine
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

        if 'server' not in self.headers:
            from pyserve import __version__
            self.headers['server'] = f'PyServe/{__version__} (Async)'

    def to_bytes(self):
        status_line = f"HTTP/1.1 {self.status_code} {HTTPStatus(self.status_code).phrase}\r\n"
        header_lines = ''.join(f"{k}: {v}\r\n" for k, v in self.headers.items())
        
        response = status_line.encode() + header_lines.encode() + b"\r\n"
        if self.body:
            response += self.body
            
        return response

class AsyncTCPServer:
    def __init__(self, host, port, backlog=5):
        self.host = host
        self.port = port
        self.backlog = backlog
        self.server = None
        self.logger = PyServeLogger()
        self.running = False

    async def start(self):
        self.server = await asyncio.start_server(
            self.handle_client, 
            self.host, 
            self.port,
            backlog=self.backlog
        )
        self.running = True
        self.logger.info(f"Server started on {self.host}:{self.port}")
        
        async with self.server:
            await self.server.serve_forever()

    async def stop(self):
        self.logger.info("Shutting down server...")
        self.running = False
        if self.server:
            self.server.close()
            await self.server.wait_closed()

    async def handle_client(self, reader, writer):
        client_addr = writer.get_extra_info('peername')
        self.logger.info(f"Connected to {client_addr[0]}:{client_addr[1]}")
        
        try:
            # Set a timeout for reading
            request_data = await asyncio.wait_for(reader.read(4096), timeout=30)
            
            if not request_data:
                return
                
            response = await self.handle_request(request_data, client_addr)
            writer.write(response.to_bytes())
            await writer.drain()
        except asyncio.TimeoutError:
            self.logger.warning(f"Timeout reading from client {client_addr}")
        except Exception as e:
            self.logger.error(f"Error handling client {client_addr}: {e}")
        finally:
            writer.close()
            await writer.wait_closed()

    async def handle_request(self, request_data, client_address):
        return HTTPResponse(
            status_code=200,
            body=b"Async TCP Server is running"
        )

class AsyncHTTPServer(AsyncTCPServer):
    def __init__(self, host, port, static_dir="./static", template_dir="./templates", 
                 backlog=5, debug=False, redirections=None, reverse_proxy=None):
        super().__init__(host, port, backlog)
        self.static_dir = os.path.abspath(static_dir)
        self.template_engine = AsyncTemplateEngine(template_dir)
        self.debug = debug
        self.redirections = get_redirections(redirections or [])
        self.reverse_proxy = reverse_proxy or []
        self.client_session = None
        
        # Create static directory if it doesn't exist
        os.makedirs(self.static_dir, exist_ok=True)
        
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
    
    async def start(self):
        # Create aiohttp client session for reverse proxy
        self.client_session = aiohttp.ClientSession()
        await super().start()
    
    async def stop(self):
        # Close aiohttp client session
        if self.client_session:
            await self.client_session.close()
        await super().stop()

    def handle_redirection(self, request):
        """
        Handles redirection request

        Args:
            request: HTTP-request
        
        Returns:
            HTTPResponse: Response with redirection
        """
        target_url = self.redirections[request.path]

        if request.query_params:
            query_parts = []
            for key, values in request.query_params.items():
                for value in values:
                    query_parts.append(f"{key}={value}")
            if query_parts:
                target_url += "?" + "&".join(query_parts)

        return HTTPResponse(302, headers={'Location': target_url})

    async def handle_request(self, request_data, client_address):
        request = HTTPRequest(request_data)
        
        if not request.method or not request.path:
            return HTTPResponse(400, body=b"Bad Request")
            
        self.logger.info(f"Received {request.method} request for {request.path} from {client_address[0]}:{client_address[1]}")

        # Check if reverse proxy is needed
        for proxy_config in self.reverse_proxy:
            proxy_path = proxy_config.get('path', '/')
            if request.path.startswith(proxy_path):
                self.logger.info(f"Proxying request {request.path} to {proxy_config['host']}:{proxy_config['port']}")
                return await self.handle_reverse_proxy(request, proxy_config)
        
        # Normal request processing if not proxying
        if request.path in self.redirections:
            self.logger.info(f"Redirecting {request.path} to {self.redirections[request.path]}")
            return self.handle_redirection(request)
        elif request.path == '/':
            return await self.handle_root(request)
        elif request.path.startswith('/static/'):
            return await self.handle_static_file(request)
        else:
            file_path = os.path.join(self.static_dir, request.path.lstrip('/'))
            if os.path.isfile(file_path):
                return await self.serve_static_file(file_path)
            else:
                return await self.error_response(404, "Not Found", f"The requested URL {request.path} was not found on this server.")

    async def handle_root(self, request):
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
                    <p>Your Async HTTP server is running successfully.</p>
                    <p>You can place static files in the <code>static</code> directory.</p>
                    <p>You can find more information about PyServe in the <a href="/docs">documentation</a>.</p>
                    <p>Or you can just visit <a href="https://github.com/ShiftyX1/PyServe">GitHub repository</a> to get more information.</p>
                    <p>And don't forget about home page in basic configuration. It's <a href="/home">here</a>.</p>
                </div>
            </div>
        </body>
        </html>
        """
        return HTTPResponse(200, body=html.encode())

    async def handle_static_file(self, request):
        file_path = os.path.normpath(os.path.join(
            self.static_dir,
            request.path.replace('/static/', '', 1)
        ))
        
        if not file_path.startswith(self.static_dir):
            self.logger.warning(f"Attempted directory traversal: {request.path}")
            return await self.error_response(403, "Forbidden", "You don't have permission to access this resource.")
            
        return await self.serve_static_file(file_path)

    async def serve_static_file(self, file_path):
        if not os.path.exists(file_path):
            self.logger.warning(f"File not found: {file_path}")
            return await self.error_response(404, "Not Found", f"The requested file {os.path.basename(file_path)} was not found.")
            
        if not os.path.isfile(file_path):
            return await self.error_response(403, "Forbidden", "You don't have permission to access this resource.")
        
        try:
            _, file_extension = os.path.splitext(file_path)
            content_type = self.content_types.get(file_extension.lower(), 'application/octet-stream')
            
            async with aiofiles.open(file_path, 'rb') as file:
                content = await file.read()
                
            headers = {
                'content-type': content_type,
                'content-length': str(len(content))
            }
            
            if self.debug:
                self.logger.debug(f"Serving static file: {file_path} ({content_type})")
            return HTTPResponse(200, headers=headers, body=content)
        except Exception as e:
            self.logger.error(f"Error serving {file_path}: {e}")
            return await self.error_response(500, "Internal Server Error", "An unexpected error occurred while processing your request.")
        
    async def error_response(self, status_code, status_text, error_details):
        error_template = await self.template_engine.render_error(status_code, status_text, error_details)
        return HTTPResponse(status_code, body=error_template.encode())
    
    async def handle_reverse_proxy(self, request, proxy_config):
        """
        Handles request through reverse proxy using aiohttp
        
        Args:
            request: HTTP-request from client
            proxy_config: Proxy server configuration (host, port, path)
            
        Returns:
            HTTPResponse: Response from proxy server
        """
        try:
            target_host = proxy_config['host']
            target_port = proxy_config['port']
            base_path = proxy_config['path']
            
            if request.path.startswith(base_path):
                target_path = request.path[len(base_path):]
                if not target_path:
                    target_path = '/'
            else:
                target_path = request.path
                
            query_string = ""
            if request.query_params:
                query_parts = []
                for key, values in request.query_params.items():
                    for value in values:
                        query_parts.append(f"{key}={value}")
                if query_parts:
                    query_string = "?" + "&".join(query_parts)
                    
            target_url = f"http://{target_host}:{target_port}{target_path}{query_string}"
                
            if self.debug:
                self.logger.debug(f"Connecting to {target_url}")
                
            # Prepare headers for proxying
            proxy_headers = {}
            for name, value in request.headers.items():
                if name.lower() not in ['connection', 'keep-alive', 'proxy-authenticate', 
                                       'proxy-authorization', 'te', 'trailers', 
                                       'transfer-encoding', 'upgrade']:
                    proxy_headers[name] = value
                    
            proxy_headers['host'] = f"{target_host}:{target_port}"
            
            client_ip = request.headers.get('x-forwarded-for', '')
            if client_ip:
                proxy_headers['x-forwarded-for'] = client_ip
            else:
                proxy_headers['x-forwarded-for'] = request.headers.get('remote_addr', '')
                
            proxy_headers['x-forwarded-host'] = request.headers.get('host', '')
            proxy_headers['x-forwarded-proto'] = 'http'
            
            if self.debug:
                self.logger.debug(f"Proxy request: {request.method} {target_url}")
                self.logger.debug(f"Proxy headers: {proxy_headers}")
            
            # Make the request using aiohttp
            async with self.client_session.request(
                method=request.method, 
                url=target_url,
                headers=proxy_headers,
                data=request.body,
                allow_redirects=False
            ) as resp:
                body = await resp.read()
                
                # Handle gzip encoding
                content_encoding = resp.headers.get('content-encoding', '').lower()
                if content_encoding == 'gzip':
                    try:
                        gzip_file = gzip.GzipFile(fileobj=io.BytesIO(body))
                        body = gzip_file.read()
                    except Exception as e:
                        self.logger.error(f"Error decompressing gzip response: {e}")
                        
                # Copy response headers
                response_headers = {}
                for header, value in resp.headers.items():
                    if header.lower() not in ['connection', 'keep-alive', 'proxy-authenticate', 
                                             'proxy-authorization', 'te', 'trailers', 
                                             'transfer-encoding']:
                        response_headers[header.lower()] = value
                        
                if content_encoding == 'gzip':
                    response_headers['content-length'] = str(len(body))
                    if 'content-encoding' in response_headers:
                        del response_headers['content-encoding']
                        
                from pyserve import __version__
                via_header = f"1.1 PyServe/{__version__} (Async Reverse Proxy)"
                response_headers['via'] = via_header
                
                return HTTPResponse(resp.status, response_headers, body)
                
        except Exception as e:
            self.logger.error(f"Async reverse proxy error: {e}")
            return await self.error_response(502, "Bad Gateway", f"Error proxying to {proxy_config['host']}:{proxy_config['port']}")