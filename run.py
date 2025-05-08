#!/usr/bin/env python3
"""
PyServe - HTTP Server Runner
"""

import os
import sys
import signal
import argparse
from pyserve import HTTPServer, Configuration, get_logger, TestConfiguration
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
  python run.py --proxy host:port/path    # Enable reverse proxy
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
    parser.add_argument('-d', '--debug', action='store_true',
                        help='Enable debug mode (more verbose logging)')
    parser.add_argument('--proxy', type=str,
                        help='Configure reverse proxy with format host:port/path')
    parser.add_argument('--test', type=str, choices=['all', 'configuration', 'directories'],
                        help='Run tests')
    
    return parser.parse_args()

def setup_signal_handlers(server):
    """Setup signal handlers for graceful shutdown"""
    def signal_handler(sig, frame):
        server.close()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

def parse_proxy_arg(proxy_arg):
    """Parse the proxy argument in the format host:port/path"""
    if not proxy_arg:
        return None
        
    try:
        if '/' in proxy_arg:
            hostport, path = proxy_arg.split('/', 1)
            if not path.startswith('/'):
                path = '/' + path
        else:
            hostport = proxy_arg
            path = '/'
            
        if ':' in hostport:
            host, port_str = hostport.split(':', 1)
            port = int(port_str)
        else:
            host = hostport
            port = 80
            
        return {
            "host": host,
            "port": port,
            "path": path
        }
    except Exception as e:
        print(f"Error parsing proxy argument: {e}")
        print("Format should be host:port/path")
        sys.exit(1)

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
    
    if args.proxy:
        proxy_config = parse_proxy_arg(args.proxy)
        if proxy_config:
            if 'reverse_proxy' not in config.server_config:
                config.server_config['reverse_proxy'] = []
            config.server_config['reverse_proxy'].append(proxy_config)

    if args.test:
        test_config = TestConfiguration()
        
        if args.test == 'all':
            load_result = test_config.test_load_config()
            if not load_result:
                logger.critical("Configuration load test failed")
                sys.exit(3)
                
            config_result = test_config.test_configuration()
            dir_result = test_config.test_static_directories()
            
            if config_result == 2:
                logger.critical("Critical configuration tests failed")
                sys.exit(2)
            elif config_result == 1:
                logger.warning("Optional configuration tests failed")
                
            if not dir_result:
                logger.warning("Directory tests failed")
                
            if config_result > 0 or not dir_result:
                sys.exit(1)
            else:
                logger.info("All tests passed successfully")
                sys.exit(0)
                
        elif args.test == 'configuration':
            load_result = test_config.test_load_config()
            if not load_result:
                sys.exit(3)
                
            config_result = test_config.test_configuration()
            sys.exit(config_result)
            
        elif args.test == 'directories':
            dir_result = test_config.test_static_directories()
            sys.exit(0 if dir_result else 1)

    # Get server configuration (command line args override config file)
    host = args.host or config.server_config.get('host')
    port = args.port or config.server_config.get('port')
    backlog = config.server_config.get('backlog')
    static_dir = args.static or config.http_config.get('static_dir')
    template_dir = args.templates or config.http_config.get('templates_dir')
    reverse_proxy = config.server_config.get('reverse_proxy', [])
    
    try:
        server = HTTPServer(
            host, 
            port, 
            static_dir, 
            template_dir, 
            backlog, 
            debug=True if args.debug else False, 
            redirections=config.redirections,
            reverse_proxy=reverse_proxy
        )
        setup_signal_handlers(server)
        from pyserve import __version__
        logger.info(f"PyServe v{__version__} starting")
        if args.debug:
            logger.debug(f"Configuration loaded: {config.server_config}")
        logger.info(f"Server running at http://{host}:{port}/")
        logger.info(f"Static files directory: {os.path.abspath(static_dir)}")
        logger.info(f"Template files directory: {os.path.abspath(template_dir)}")
        
        if reverse_proxy:
            for proxy in reverse_proxy:
                logger.info(f"Reverse proxy configured: {proxy['path']} -> {proxy['host']}:{proxy['port']}")
                
        server.run()
    except Exception as e:
        logger.critical(f"Failed to start server: {e}")
        if isinstance(e, PermissionError):
            logger.warning("Permission denied: Please run the server with sudo privileges (or maybe you should change the default HTTP port in config.yaml)")
        sys.exit(1)

if __name__ == "__main__":
    run()