#!/usr/bin/env python3
"""
Reset the PostgreSQL database by dropping and recreating all tables
"""

import os
import sys
import logging
import argparse
from python.src.gdelt.database.postgres_adapter import get_postgres_adapter
from python.src.gdelt.config.database_config import get_database_config

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def reset_database(config_path=None):
    """
    Reset the PostgreSQL database by dropping and recreating all tables
    
    Args:
        config_path: Path to database configuration file
    """
    # Get database configuration
    db_config = get_database_config(config_path)
    
    # Connect to PostgreSQL database
    db = get_postgres_adapter(**db_config['postgres'])
    
    # Reset database
    db.reset_database()
    
    logger.info("Database reset successfully")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Reset the PostgreSQL database')
    parser.add_argument('--config-path', type=str, default='config/database.json',
                        help='Path to database configuration file')
    args = parser.parse_args()
    
    reset_database(args.config_path)

if __name__ == '__main__':
    main()
