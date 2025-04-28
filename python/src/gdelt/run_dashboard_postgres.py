#!/usr/bin/env python3
"""
Run the GDELT News Analysis Dashboard with PostgreSQL support
"""

import os
import sys
import argparse
import logging
import subprocess
import webbrowser
from time import sleep

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Run GDELT News Analysis Dashboard with PostgreSQL')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to')
    parser.add_argument('--config-path', help='Path to database configuration file')
    parser.add_argument('--analysis-dir', help='Path to the analysis directory')
    parser.add_argument('--no-browser', action='store_true', help='Do not open browser automatically')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    return parser.parse_args()

def main():
    """Main entry point"""
    args = parse_args()
    
    # Get the path to the server script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    server_script = os.path.join(script_dir, 'visualizer', 'server_postgres.py')
    
    # Build command
    cmd = [sys.executable, server_script, '--host', args.host, '--port', str(args.port)]
    
    if args.config_path:
        cmd.extend(['--config-path', args.config_path])
    
    if args.analysis_dir:
        cmd.extend(['--analysis-dir', args.analysis_dir])
    
    if args.debug:
        cmd.append('--debug')
    
    # Log command
    logger.info(f"Running command: {' '.join(cmd)}")
    
    # Start server
    process = subprocess.Popen(cmd)
    
    try:
        # Wait for server to start
        logger.info(f"Waiting for server to start on http://{args.host}:{args.port}...")
        sleep(2)
        
        # Open browser
        if not args.no_browser:
            url = f"http://{args.host}:{args.port}"
            logger.info(f"Opening browser at {url}")
            webbrowser.open(url)
        
        # Wait for server to exit
        process.wait()
    except KeyboardInterrupt:
        logger.info("Stopping server...")
        process.terminate()
        process.wait()
    
    logger.info("Server stopped")

if __name__ == "__main__":
    main()
