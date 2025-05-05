#!/usr/bin/env python3
"""
PyServe - HTTP Server Runner
"""

import os
import sys
import signal
import argparse
from pyserve import HTTPServer, Configuration, get_logger
from pyserve import __version__

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='PyServe - Simple HTTP Server\nVersion {}'.format(__version__),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run.py                           # Run with default settings
  python run.py -p 8080                   # Run on port 8080
  python run.py -H 0.0.0.0 -p 8000        # Run on all interfaces
  python run.py -s ./my_static            # Use custom static directory
  python run.py -t ./my_templates         # Use custom templates directory
  python run.py -c /path/to/config.yaml   # Use custom config file
"""
    )
    
    parser.add_argument('-c', '--config', type=str, default='./config.yaml',
                        help='Path to configuration file')
    parser.add_argument('-p', '--port', type=int,
                        help='Port to run the server on (overrides config)')
    parser.add_argument('-H', '--host', type=str,
                        help='Host to bind to (overrides config)')
    parser.add_argument('-s', '--static', type=str,
                        help='Directory for static files (overrides config)')
    parser.add_argument('-t', '--templates', type=str,
                        help='Directory for template files (overrides config)')
    parser.add_argument('-v', '--version', action='store_true',
                        help='Show PyServe version and exit')
    
    return parser.parse_args()

def setup_signal_handlers(server):
    """Setup signal handlers for graceful shutdown"""
    def signal_handler(sig, frame):
        print("\nShutting down server...")
        server.close()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

def run():
    """Run the HTTP server"""
    # Parse arguments
    args = parse_arguments()
    
    # Check for version flag
    if args.version:
        from pyserve import __version__
        print(f"PyServe version {__version__}")
        sys.exit(0)
    
    config = Configuration(args.config)
    
    # Setup logger
    logger = get_logger(
        level=config.get_log_level(),
        log_file=config.logging_config.get('log_file')
    )
    
    # Get server configuration (command line args override config file)
    host = args.host or config.server_config.get('host', '127.0.0.1')
    port = args.port or config.server_config.get('port', 8000)
    backlog = config.server_config.get('backlog', 5)
    static_dir = args.static or config.http_config.get('static_dir', './static')
    template_dir = args.templates or config.http_config.get('templates_dir', './templates')
    
    # Create and start the server
    try:
        server = HTTPServer(host, port, static_dir, template_dir, backlog)
        setup_signal_handlers(server)
        logger.info(f"PyServe v1.0.0 starting")
        logger.info(f"Server running at http://{host}:{port}/")
        logger.info(f"Static files directory: {os.path.abspath(static_dir)}")
        logger.info(f"Template files directory: {os.path.abspath(template_dir)}")
        server.run()
    except Exception as e:
        logger.critical(f"Failed to start server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run()