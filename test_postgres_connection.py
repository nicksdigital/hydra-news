#!/usr/bin/env python3
"""
Test PostgreSQL Connection

This script tests the connection to the PostgreSQL database.
"""

import os
import sys
import json
import logging
import argparse

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_connection(host, port, dbname, user, password):
    """
    Test connection to PostgreSQL database
    
    Args:
        host: Database host
        port: Database port
        dbname: Database name
        user: Database user
        password: Database password
    """
    try:
        import psycopg2
        
        # Connect to PostgreSQL
        logger.info(f"Connecting to PostgreSQL database: {dbname} on {host}:{port} as {user}")
        conn = psycopg2.connect(
            host=host,
            port=port,
            dbname=dbname,
            user=user,
            password=password
        )
        
        # Test connection
        cursor = conn.cursor()
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        logger.info(f"Connected to PostgreSQL: {version}")
        
        # Close connection
        cursor.close()
        conn.close()
        
        logger.info("Connection test successful")
        return True
    
    except ImportError:
        logger.error("psycopg2 module not found. Please install it with: pip install psycopg2-binary")
        return False
    
    except Exception as e:
        logger.error(f"Error connecting to PostgreSQL: {e}")
        return False

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Test PostgreSQL connection')
    parser.add_argument('--config-path', type=str, default='config/database.json',
                        help='Path to database configuration file')
    parser.add_argument('--host', type=str,
                        help='PostgreSQL host')
    parser.add_argument('--port', type=int,
                        help='PostgreSQL port')
    parser.add_argument('--dbname', type=str,
                        help='PostgreSQL database name')
    parser.add_argument('--user', type=str,
                        help='PostgreSQL user')
    parser.add_argument('--password', type=str,
                        help='PostgreSQL password')
    args = parser.parse_args()
    
    # Get configuration from file
    config = {}
    if os.path.exists(args.config_path):
        try:
            with open(args.config_path, 'r') as f:
                config = json.load(f)
            logger.info(f"Loaded configuration from {args.config_path}")
        except Exception as e:
            logger.error(f"Error loading configuration from {args.config_path}: {e}")
    
    # Get PostgreSQL configuration
    host = args.host or config.get('postgres', {}).get('host', 'localhost')
    port = args.port or config.get('postgres', {}).get('port', 5432)
    dbname = args.dbname or config.get('postgres', {}).get('dbname', 'gdelt_news')
    user = args.user or config.get('postgres', {}).get('user', 'postgres')
    password = args.password or config.get('postgres', {}).get('password', 'postgres')
    
    # Test connection
    success = test_connection(host, port, dbname, user, password)
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
