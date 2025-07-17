# PyServe

PyServe is a modern, async HTTP server written in Python. Originally created for educational purposes, it has evolved into a powerful tool for rapid prototyping and serving web applications with unique features like AI-generated content.

<img src="./images/logo.png" alt="isolated" width="150"/>

[Project Roadmap](./roadmap.md)

## Project Overview

PyServe v0.4.2 introduces a completely refactored architecture with modern async/await syntax and new exciting features like **Vibe-Serving** - AI-powered dynamic content generation.

### Key Features:

- **Async HTTP Server** - Built with Python's asyncio for high performance
- **Advanced Configuration System V2** - Powerful extensible configuration with full backward compatibility
- **Regex Routing & SPA Support** - nginx-style routing patterns with Single Page Application fallback
- **Static File Serving** - Efficient serving with correct MIME types
- **Template System** - Dynamic content generation
- **Vibe-Serving Mode** - AI-generated content using language models (OpenAI, Claude, etc.)
- **Reverse Proxy** - Forward requests to backend services with advanced routing
- **SSL/HTTPS Support** - Secure connections with certificate configuration
- **Modular Extensions** - Plugin-like architecture for security, caching, monitoring
- **Beautiful Logging** - Colored terminal output with file rotation
- **Error Handling** - Styled error pages and graceful fallbacks

## Getting Started

### Prerequisites

- Python 3.7 or higher
- Dependencies: `pip install -r requirements.txt`

### Installation

```bash
git clone https://github.com/ShiftyX1/PyServe.git
cd PyServe
pip install -r requirements.txt
```

### Running the Server

Basic startup:
```bash
python run.py
```

Running with specific configuration:
```bash
python run.py -H 0.0.0.0 -p 8080
```

**NEW: Vibe-Serving Mode (AI-Generated Content):**
```bash
python run.py --vibe-serving
```

### Command Line Options

| Option | Description |
|--------|-------------|
| `-h, --help` | Show help and exit |
| `-c, --config CONFIG` | Path to configuration file |
| `-p, --port PORT` | Port to run the server on |
| `-H, --host HOST` | Host to bind the server to |
| `-s, --static STATIC` | Directory for static files |
| `-t, --templates TEMPLATES` | Directory for templates |
| `-v, --version` | Show version and exit |
| `-d, --debug` | Enable debug mode |
| `--ssl` | Enable SSL/HTTPS |
| `--cert CERT` | SSL certificate file |
| `--key KEY` | SSL private key file |
| `--proxy HOST:PORT/PATH` | Configure reverse proxy |
| `--vibe-serving` | **NEW:** Enable AI-generated content mode |
| `--skip-proxy-check` | Skip proxy availability check |

## Vibe-Serving: AI-Generated Content

PyServe v0.4.2 introduces **Vibe-Serving** - a revolutionary feature that generates web pages on-the-fly using AI language models.

### How it works:
1. Configure routes and prompts in `vibeconfig.yaml`
2. Set your `OPENAI_API_KEY` environment variable
3. Start with `python run.py --vibe-serving`
4. Visit any configured route to see AI-generated content

### Example vibeconfig.yaml:
```yaml
routes:
  "/": "Generate a modern landing page for PyServe"
  "/about": "Create an about page describing the project"
  "/contact": "Generate a contact page with form"

settings:
  cache_ttl: 3600
  model: "gpt-4"
  timeout: 30
```

## Configuration

PyServe supports two configuration formats with **full backward compatibility**:

### V1 Configuration (Legacy - still supported)

```yaml
server:
  host: 127.0.0.1
  port: 8000
  backlog: 5

http:
  static_dir: ./static
  templates_dir: ./templates

ssl:
  enabled: false

logging:
  level: INFO
```

### V2 Configuration (Recommended)

The new V2 configuration system adds powerful extensions while maintaining full V1 compatibility:

```yaml
version: 2

# Core modules (same as V1)
server:
  host: 0.0.0.0
  port: 8080

http:
  static_dir: ./static
  templates_dir: ./templates

# NEW: Extensions system
extensions:
  - type: routing
    config:
      regex_locations:
        # API with version capture
        "~^/api/v(?P<version>\\d+)/":
          proxy_pass: "http://backend:3000"
          headers:
            - "API-Version: {version}"
        
        # Static files with caching
        "~*\\.(js|css|png|jpg)$":
          root: "./static"
          cache_control: "max-age=31536000"
        
        # SPA fallback
        "__default__":
          spa_fallback: true
          root: "./dist"
```

#### Key V2 Features:

- **Regex Routing** - nginx-style patterns with priorities
- **SPA Support** - Automatic fallback for Single Page Applications  
- **Parameter Capture** - Extract URL parameters with named groups
- **External Modules** - Load extensions from separate files
- **Graceful Degradation** - Errors in extensions don't break core functionality

📖 **[Complete V2 Configuration Guide](./CONFIGURATION_V2_GUIDE.md)** - Detailed documentation with examples

### Quick V2 Examples

#### Simple SPA Application
```yaml
version: 2
server:
  host: 0.0.0.0
  port: 8080
http:
  static_dir: ./static
extensions:
  - type: routing
    config:
      regex_locations:
        "~^/api/": { proxy_pass: "http://localhost:3000" }
        "__default__": { spa_fallback: true, root: "./dist" }
```

#### Microservices Gateway
```yaml
version: 2
extensions:
  - type: routing
    config:
      regex_locations:
        "~^/api/users/": { proxy_pass: "http://user-service:3001" }
        "~^/api/orders/": { proxy_pass: "http://order-service:3002" }
        "=/health": { return: "200 OK" }
```

### Main Configuration (config.yaml)

```yaml
server:
  host: 127.0.0.1
  port: 8000
  backlog: 5
  redirect_instructions:
    - /home: /index.html

http:
  static_dir: ./static
  templates_dir: ./templates

ssl:
  enabled: false
  cert_file: ./ssl/cert.pem
  key_file: ./ssl/key.pem

logging:
  level: INFO
  log_file: ./logs/pyserve.log
  console_output: true
  use_colors: true
```

### Vibe Configuration (vibeconfig.yaml)

For AI-generated content mode:

```yaml
routes:
  "/": "Create a beautiful landing page"
  "/about": "Generate an about page"

settings:
  cache_ttl: 3600
  model: "gpt-4"
  api_url: "https://api.openai.com/v1"  # Optional custom endpoint
```

## Architecture

PyServe v0.4.2 features a modular architecture:

- **Core** - Base server components and configuration
- **HTTP** - Request/response handling and routing  
- **Template** - Dynamic content rendering
- **Vibe** - AI-powered content generation
- **Utils** - Helper functions and utilities

## Use Cases

- **Modern Web Applications** - SPA hosting with API proxying
- **Microservices Gateway** - Route requests to multiple backend services
- **Development** - Quick local development server with hot-reload friendly routing
- **Prototyping** - Rapid testing with regex-based routing
- **Education** - Learning HTTP protocol, routing, and server architecture
- **AI Experimentation** - Testing AI-generated web content with Vibe-Serving
- **Static Sites** - Advanced static file serving with caching rules
- **Reverse Proxy** - Development and production proxy setup with pattern matching

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is distributed under the MIT license.