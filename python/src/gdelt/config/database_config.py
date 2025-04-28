#!/usr/bin/env python3
"""
Database Configuration for GDELT News Analysis

This module provides database configuration functionality for the GDELT News Analysis system.
"""

import os
import json
import logging
import argparse

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Default configuration
DEFAULT_CONFIG = {
    'postgres': {
        'host': 'localhost',
        'port': 5432,
        'dbname': 'gdelt_news',
        'user': 'postgres',
        'password': 'adv62062',
        'min_conn': 1,
        'max_conn': 10
    }
}

def get_database_config(config_path=None):
    """
    Get database configuration

    Args:
        config_path: Path to configuration file (optional)

    Returns:
        Database configuration dictionary
    """
    # Start with default configuration
    config = DEFAULT_CONFIG.copy()

    # Update PostgreSQL configuration from environment variables
    if os.environ.get('POSTGRES_HOST'):
        config['postgres']['host'] = os.environ.get('POSTGRES_HOST')
    if os.environ.get('POSTGRES_PORT'):
        config['postgres']['port'] = int(os.environ.get('POSTGRES_PORT'))
    if os.environ.get('POSTGRES_DB'):
        config['postgres']['dbname'] = os.environ.get('POSTGRES_DB')
    if os.environ.get('POSTGRES_USER'):
        config['postgres']['user'] = os.environ.get('POSTGRES_USER')
    if os.environ.get('POSTGRES_PASSWORD'):
        config['postgres']['password'] = os.environ.get('POSTGRES_PASSWORD')

    # Load configuration from file if provided
    if config_path and os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                file_config = json.load(f)

                # Update configuration from file
                if 'use_postgres' in file_config:
                    config['use_postgres'] = file_config['use_postgres']

                if 'postgres' in file_config:
                    config['postgres'].update(file_config['postgres'])

                if 'sqlite' in file_config:
                    config['sqlite'].update(file_config['sqlite'])

                logger.info(f"Loaded database configuration from {config_path}")
        except Exception as e:
            logger.error(f"Error loading configuration from {config_path}: {e}")

    return config

def save_database_config(config, config_path):
    """
    Save database configuration to file

    Args:
        config: Database configuration dictionary
        config_path: Path to save configuration file
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(config_path), exist_ok=True)

        # Save configuration to file
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)

        logger.info(f"Saved database configuration to {config_path}")
    except Exception as e:
        logger.error(f"Error saving configuration to {config_path}: {e}")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Database configuration for GDELT News Analysis')
    parser.add_argument('--config-path', type=str, default='config/database.json',
                        help='Path to configuration file')
    parser.add_argument('--use-postgres', action='store_true',
                        help='Use PostgreSQL instead of SQLite')
    parser.add_argument('--postgres-host', type=str,
                        help='PostgreSQL host')
    parser.add_argument('--postgres-port', type=int,
                        help='PostgreSQL port')
    parser.add_argument('--postgres-db', type=str,
                        help='PostgreSQL database name')
    parser.add_argument('--postgres-user', type=str,
                        help='PostgreSQL user')
    parser.add_argument('--postgres-password', type=str,
                        help='PostgreSQL password')
    parser.add_argument('--sqlite-db-path', type=str,
                        help='SQLite database path')
    parser.add_argument('--save', action='store_true',
                        help='Save configuration to file')
    args = parser.parse_args()

    # Get configuration
    config = get_database_config(args.config_path)

    # Update configuration from command line arguments
    if args.use_postgres is not None:
        config['use_postgres'] = args.use_postgres

    if args.postgres_host:
        config['postgres']['host'] = args.postgres_host
    if args.postgres_port:
        config['postgres']['port'] = args.postgres_port
    if args.postgres_db:
        config['postgres']['dbname'] = args.postgres_db
    if args.postgres_user:
        config['postgres']['user'] = args.postgres_user
    if args.postgres_password:
        config['postgres']['password'] = args.postgres_password

    if args.sqlite_db_path:
        config['sqlite']['db_path'] = args.sqlite_db_path

    # Print configuration
    print(json.dumps(config, indent=2))

    # Save configuration if requested
    if args.save:
        save_database_config(config, args.config_path)

if __name__ == '__main__':
    main()
