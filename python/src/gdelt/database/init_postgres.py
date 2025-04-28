#!/usr/bin/env python3
"""
Initialize PostgreSQL Database for GDELT News Analysis

This script initializes the PostgreSQL database for the GDELT News Analysis system.
"""

import os
import sys
import logging
import argparse
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_database(host, port, user, password, dbname):
    """
    Create a PostgreSQL database
    
    Args:
        host: Database host
        port: Database port
        user: Database user
        password: Database password
        dbname: Database name to create
    """
    # Connect to PostgreSQL server
    conn = None
    try:
        # Connect to default database
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            dbname='postgres'
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (dbname,))
        exists = cursor.fetchone()
        
        if not exists:
            # Create database
            cursor.execute(f"CREATE DATABASE {dbname}")
            logger.info(f"Created database: {dbname}")
        else:
            logger.info(f"Database already exists: {dbname}")
        
        cursor.close()
    
    except Exception as e:
        logger.error(f"Error creating database: {e}")
        raise
    
    finally:
        if conn:
            conn.close()

def create_user(host, port, admin_user, admin_password, new_user, new_password, dbname):
    """
    Create a PostgreSQL user and grant privileges
    
    Args:
        host: Database host
        port: Database port
        admin_user: Admin user
        admin_password: Admin password
        new_user: New user to create
        new_password: New user's password
        dbname: Database name to grant privileges on
    """
    # Connect to PostgreSQL server
    conn = None
    try:
        # Connect to default database
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=admin_user,
            password=admin_password,
            dbname='postgres'
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (new_user,))
        exists = cursor.fetchone()
        
        if not exists:
            # Create user
            cursor.execute(f"CREATE USER {new_user} WITH PASSWORD '{new_password}'")
            logger.info(f"Created user: {new_user}")
        else:
            logger.info(f"User already exists: {new_user}")
        
        # Grant privileges
        cursor.execute(f"GRANT ALL PRIVILEGES ON DATABASE {dbname} TO {new_user}")
        logger.info(f"Granted privileges on database {dbname} to user {new_user}")
        
        cursor.close()
    
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise
    
    finally:
        if conn:
            conn.close()

def initialize_database(host, port, user, password, dbname):
    """
    Initialize the PostgreSQL database
    
    Args:
        host: Database host
        port: Database port
        user: Database user
        password: Database password
        dbname: Database name
    """
    # Import here to avoid circular imports
    from python.src.gdelt.database.postgres_adapter import get_postgres_adapter
    
    # Get PostgreSQL adapter
    adapter = get_postgres_adapter(
        host=host,
        port=port,
        dbname=dbname,
        user=user,
        password=password
    )
    
    # Create tables
    adapter.create_tables()
    
    # Close adapter
    adapter.close()

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Initialize PostgreSQL database for GDELT News Analysis')
    parser.add_argument('--host', type=str, default='localhost', help='Database host')
    parser.add_argument('--port', type=int, default=5432, help='Database port')
    parser.add_argument('--admin-user', type=str, default='postgres', help='Admin user')
    parser.add_argument('--admin-password', type=str, default='postgres', help='Admin password')
    parser.add_argument('--user', type=str, default='gdelt_user', help='Database user')
    parser.add_argument('--password', type=str, default='gdelt_password', help='Database password')
    parser.add_argument('--dbname', type=str, default='gdelt_news', help='Database name')
    parser.add_argument('--create-db', action='store_true', help='Create database')
    parser.add_argument('--create-user', action='store_true', help='Create user')
    parser.add_argument('--init-tables', action='store_true', help='Initialize tables')
    parser.add_argument('--all', action='store_true', help='Perform all initialization steps')
    args = parser.parse_args()
    
    # Perform initialization steps
    if args.create_db or args.all:
        create_database(args.host, args.port, args.admin_user, args.admin_password, args.dbname)
    
    if args.create_user or args.all:
        create_user(args.host, args.port, args.admin_user, args.admin_password, args.user, args.password, args.dbname)
    
    if args.init_tables or args.all:
        initialize_database(args.host, args.port, args.user, args.password, args.dbname)
    
    logger.info("Database initialization completed")

if __name__ == '__main__':
    main()
