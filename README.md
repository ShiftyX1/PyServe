# PyServe

PyServe is a lightweight HTTP server written in Python for educational purposes. The project demonstrates a basic implementation of an HTTP server from scratch, using only the Python standard library.

<img src="./images/logo.png" alt="isolated" width="150"/>

[Project Roadmap](./roadmap.md)

## Project Overview

I developed PyServe as a learning project to understand the principles of HTTP servers. It is not intended for use in a production environment, but contains all the basic components of a real HTTP server and is suitable for learning and experimentation.

### Features:

- Simple and understandable HTTP server without external dependencies (almost without)
- Serving static files with correct MIME types
- Template support for generating dynamic content
- Customizable logging with colored terminal output
- Flexible configuration via YAML files or command line arguments
- Styled error pages (404, 500, 403, etc.)
- Redirect instructions (http 301)

## Getting Started

### Prerequisites

- Python 3.7 or higher
- No external dependencies

### Running the Server

Basic startup:
```bash
./run.py
```

Running with specified port and host:
```bash
./run.py -H 0.0.0.0 -p 8080
```

Running with custom directories:
```bash
./run.py -s ./my_static -t ./my_templates
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

## Configuration

Server settings can be defined in the `config.yaml` file:

```yaml
server:
  host: 127.0.0.1
  port: 8000
  backlog: 5
  redirect_instructions:
  - /home: /index.html # /from: /to

http:
  static_dir: ./static
  templates_dir: ./templates

logging:
  level: DEBUG
  log_file: ./logs/pyserve.log
  console_output: true
```

## Educational Aspects

This project helps learn the following concepts:

- Network programming in Python (sockets, TCP/IP)
- HTTP protocol and its implementation
- Multi-threaded programming
- File handling and MIME types
- Template systems
- Error handling
- Application configuration and logging

## Possible Improvements

- Adding HTTPS support
- Implementing basic authentication
- Adding request routing capabilities (WIP right now)
- WebSocket support
- Static file caching
- Adding Gzip compression

## Notes

This project was created as part of my learning process in server development. I wanted to understand how web servers work without relying on existing frameworks. PyServe does not claim to have the performance or security of real web servers like Nginx or Apache, but it provides a good foundation for understanding their operation.

## License

This project is distributed under the MIT license.