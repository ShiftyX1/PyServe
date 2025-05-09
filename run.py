#!/usr/bin/env python3
"""
PyServe - Async HTTP Server Runner
"""

import os
import sys
import signal
import argparse
import asyncio
from pyserve import AsyncHTTPServer, Configuration, get_logger, TestConfiguration
from pyserve import __version__


def parse_arguments():
    parser = argparse.ArgumentParser(
        description='PyServe - Async HTTP Server\nVersion {}'.format(__version__),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run.py                       # Run with default settings
  python run.py -p 8080               # Run on port 8080
  python run.py -H 0.0.0.0 -p 8000    # Run on all interfaces
  python run.py -s ./my_static        # Use custom static directory
  python run.py -t ./my_templates     # Use custom templates directory
  python run.py -c /path/to/config.yaml  # Use custom config file
  python run.py --proxy host:port/path   # Enable reverse proxy
  python run.py --ssl --cert ./ssl/cert.pem --key ./ssl/key.pem  # Run with HTTPS
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
    
    ssl_group = parser.add_argument_group('SSL Options')
    ssl_group.add_argument('--ssl', action='store_true',
                        help='Enable SSL/TLS (HTTPS)')
    ssl_group.add_argument('--cert', type=str,
                        help='Path to SSL certificate file')
    ssl_group.add_argument('--key', type=str,
                        help='Path to SSL private key file')
    ssl_group.add_argument('--ssl-config', action='store_true',
                        help='Configure SSL settings in the config file and exit')
    
    return parser.parse_args()

def setup_signal_handlers(loop, server):
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(
            sig,
            lambda: asyncio.create_task(shutdown(loop, server))
        )

async def shutdown(loop, server):
    await server.stop()
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    
    for task in tasks:
        task.cancel()
    
    await asyncio.gather(*tasks, return_exceptions=True)
    loop.stop()

def parse_proxy_arg(proxy_arg):
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

async def run_server():
    args = parse_arguments()
    
    if args.version:
        print(f"PyServe version {__version__}")
        sys.exit(0)
    
    config = Configuration(args.config)
    
    log_level = config.get_log_level()
    logger_config = config.logging_config
    logger = get_logger(
        level=log_level,
        log_file=logger_config.get('log_file'),
        console_output=logger_config.get('console_output', True),
        use_colors=logger_config.get('use_colors', True),
        use_rotation=logger_config.get('use_rotation', False),
        max_log_size=logger_config.get('max_log_size', 10485760),
        backup_count=logger_config.get('backup_count', 5),
        structured_logs=logger_config.get('structured_logs', False)
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
            exit_code = test_config.run_all_tests()
            sys.exit(exit_code)
                
        elif args.test == 'configuration':
            load_result = test_config.test_load_config()
            if not load_result:
                sys.exit(3)
                
            config_result = test_config.test_configuration()
            sys.exit(config_result)
            
        elif args.test == 'directories':
            dir_result = test_config.test_static_directories()
            sys.exit(0 if dir_result else 1)

    if args.ssl_config:
        if not args.ssl or not args.cert or not args.key:
            logger.error("To configure SSL, you must provide --ssl, --cert and --key options")
            sys.exit(1)
            
        if not os.path.isfile(args.cert):
            logger.error(f"SSL certificate file not found: {args.cert}")
            sys.exit(1)
            
        if not os.path.isfile(args.key):
            logger.error(f"SSL key file not found: {args.key}")
            sys.exit(1)
            
        config.configure_ssl(enabled=True, cert_file=args.cert, key_file=args.key)
        logger.info(f"SSL configuration saved to {config.config_path}")
        sys.exit(0)
    
    host = args.host or config.server_config.get('host')
    port = args.port or config.server_config.get('port')
    backlog = config.server_config.get('backlog')
    static_dir = args.static or config.http_config.get('static_dir')
    template_dir = args.templates or config.http_config.get('templates_dir')
    reverse_proxy = config.server_config.get('reverse_proxy', [])
    
    use_ssl = args.ssl or config.ssl_config.enabled
    ssl_cert = None
    ssl_key = None
    
    if use_ssl:
        ssl_cert = args.cert or config.ssl_config.cert_file
        ssl_key = args.key or config.ssl_config.key_file
        
        if not ssl_cert or not os.path.isfile(ssl_cert):
            logger.error(f"SSL certificate file not found: {ssl_cert}")
            logger.info("Disabling SSL. Run with --ssl, --cert and --key to specify valid certificate files.")
            use_ssl = False
            ssl_cert = None
            ssl_key = None
        elif not ssl_key or not os.path.isfile(ssl_key):
            logger.error(f"SSL key file not found: {ssl_key}")
            logger.info("Disabling SSL. Run with --ssl, --cert and --key to specify valid certificate files.")
            use_ssl = False
            ssl_cert = None
            ssl_key = None
    
    try:
        loop = asyncio.get_event_loop()
        
        server = AsyncHTTPServer(
            host, 
            port, 
            static_dir, 
            template_dir, 
            backlog, 
            debug=args.debug or log_level <= 10,
            redirections=config.redirections,
            reverse_proxy=reverse_proxy,
            ssl_cert=ssl_cert,
            ssl_key=ssl_key
        )
        
        setup_signal_handlers(loop, server)
        
        protocol = "HTTPS" if use_ssl else "HTTP"
        logger.info(f"PyServe v{__version__} (Async {protocol}) starting")
        if args.debug:
            logger.debug(f"Configuration loaded: {config.server_config}")
        
        protocol_url = "https" if use_ssl else "http"
        logger.info(f"Server running at {protocol_url}://{host}:{port}/")
        logger.info(f"Static files directory: {os.path.abspath(static_dir)}")
        logger.info(f"Template files directory: {os.path.abspath(template_dir)}")
        
        if use_ssl:
            logger.info(f"SSL enabled with certificate: {ssl_cert}")
            
        if reverse_proxy:
            for proxy in reverse_proxy:
                logger.info(f"Reverse proxy configured: {proxy['path']} -> {proxy['host']}:{proxy['port']}")
        
        try:
            await server.start()
        except asyncio.exceptions.CancelledError:
            logger.info("Server was cancelled by user")
            sys.exit(0)
        except Exception as e:
            logger.critical(f"Failed to start server: {e}")
            sys.exit(1)
        
    except Exception as e:
        logger.critical(f"Failed to start server: {e}")
        if isinstance(e, PermissionError):
            logger.warning("Permission denied: Please run the server with sudo privileges (or maybe you should change the default HTTP port in config.yaml)")
        sys.exit(1)

def main():
    try:
        asyncio.run(run_server())
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()