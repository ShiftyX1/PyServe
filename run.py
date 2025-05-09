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
  python async_run.py                       # Run with default settings
  python async_run.py -p 8080               # Run on port 8080
  python async_run.py -H 0.0.0.0 -p 8000    # Run on all interfaces
  python async_run.py -s ./my_static        # Use custom static directory
  python async_run.py -t ./my_templates     # Use custom templates directory
  python async_run.py -c /path/to/config.yaml  # Use custom config file
  python async_run.py --proxy host:port/path   # Enable reverse proxy
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
        from pyserve import __version__
        print(f"PyServe version {__version__}")
        sys.exit(0)
    
    config = Configuration(args.config)
    
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

    host = args.host or config.server_config.get('host')
    port = args.port or config.server_config.get('port')
    backlog = config.server_config.get('backlog')
    static_dir = args.static or config.http_config.get('static_dir')
    template_dir = args.templates or config.http_config.get('templates_dir')
    reverse_proxy = config.server_config.get('reverse_proxy', [])
    
    try:
        loop = asyncio.get_event_loop()
        
        server = AsyncHTTPServer(
            host, 
            port, 
            static_dir, 
            template_dir, 
            backlog, 
            debug=True if args.debug else False, 
            redirections=config.redirections,
            reverse_proxy=reverse_proxy
        )
        
        setup_signal_handlers(loop, server)
        
        from pyserve import __version__
        logger.info(f"PyServe v{__version__} (Async) starting")
        if args.debug:
            logger.debug(f"Configuration loaded: {config.server_config}")
        logger.info(f"Server running at http://{host}:{port}/")
        logger.info(f"Static files directory: {os.path.abspath(static_dir)}")
        logger.info(f"Template files directory: {os.path.abspath(template_dir)}")
        
        if reverse_proxy:
            for proxy in reverse_proxy:
                logger.info(f"Reverse proxy configured: {proxy['path']} -> {proxy['host']}:{proxy['port']}")
        
        await server.start()
        
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