#!/usr/bin/env python3
"""
Migrate data from SQLite to PostgreSQL

This script migrates data from a SQLite database to a PostgreSQL database.
"""

import os
import sys
import sqlite3
import logging
import argparse
import pandas as pd
from tqdm import tqdm
from python.src.gdelt.database.postgres_adapter import get_postgres_adapter
from python.src.gdelt.config.database_config import get_database_config

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_sqlite_connection(sqlite_path):
    """
    Get a SQLite connection
    
    Args:
        sqlite_path: Path to the SQLite database file
        
    Returns:
        SQLite connection object
    """
    conn = sqlite3.connect(sqlite_path)
    conn.row_factory = sqlite3.Row
    return conn

def migrate_table(sqlite_conn, postgres_adapter, table_name, batch_size=1000):
    """
    Migrate a table from SQLite to PostgreSQL
    
    Args:
        sqlite_conn: SQLite connection object
        postgres_adapter: PostgreSQL adapter object
        table_name: Name of the table to migrate
        batch_size: Number of rows to migrate at once
        
    Returns:
        Number of rows migrated
    """
    logger.info(f"Migrating table: {table_name}")
    
    # Get table schema from SQLite
    cursor = sqlite_conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row['name'] for row in cursor.fetchall()]
    
    # Count rows in SQLite table
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    total_rows = cursor.fetchone()[0]
    logger.info(f"Total rows in {table_name}: {total_rows}")
    
    # Migrate data in batches
    rows_migrated = 0
    for offset in tqdm(range(0, total_rows, batch_size), desc=f"Migrating {table_name}"):
        # Get batch of data from SQLite
        cursor.execute(f"SELECT * FROM {table_name} LIMIT {batch_size} OFFSET {offset}")
        rows = cursor.fetchall()
        
        if not rows:
            break
        
        # Convert rows to list of dictionaries
        data = []
        for row in rows:
            data.append({column: row[column] for column in columns})
        
        # Create DataFrame from data
        df = pd.DataFrame(data)
        
        # Insert data into PostgreSQL
        for _, row in df.iterrows():
            # Create placeholders for SQL query
            placeholders = ', '.join(['%s'] * len(columns))
            columns_str = ', '.join(columns)
            
            # Create values list
            values = [row[column] for column in columns]
            
            # Insert row into PostgreSQL
            postgres_adapter.execute_query(
                f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders}) ON CONFLICT DO NOTHING",
                values,
                fetch=False
            )
        
        rows_migrated += len(rows)
    
    logger.info(f"Migrated {rows_migrated} rows from {table_name}")
    return rows_migrated

def migrate_sqlite_to_postgres(sqlite_path, postgres_config=None):
    """
    Migrate data from SQLite to PostgreSQL
    
    Args:
        sqlite_path: Path to the SQLite database file
        postgres_config: PostgreSQL configuration dictionary
        
    Returns:
        True if migration was successful, False otherwise
    """
    try:
        # Connect to SQLite database
        sqlite_conn = get_sqlite_connection(sqlite_path)
        
        # Get PostgreSQL adapter
        if postgres_config:
            postgres_adapter = get_postgres_adapter(**postgres_config)
        else:
            # Use default configuration
            db_config = get_database_config()
            postgres_adapter = get_postgres_adapter(**db_config['postgres'])
        
        # Create tables in PostgreSQL
        postgres_adapter.create_tables()
        
        # Get list of tables from SQLite
        cursor = sqlite_conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        tables = [row['name'] for row in cursor.fetchall()]
        
        # Map SQLite table names to PostgreSQL table names
        table_mapping = {
            'processed_chunks': 'chunks',
            'articles': 'articles',
            'entities': 'entities',
            'article_entities': 'article_entities',
            'sources': 'sources',
            'themes': 'themes'
        }
        
        # Migrate each table
        total_rows_migrated = 0
        for table in tables:
            if table in table_mapping:
                postgres_table = table_mapping[table]
                rows_migrated = migrate_table(sqlite_conn, postgres_adapter, table, postgres_table)
                total_rows_migrated += rows_migrated
        
        logger.info(f"Migration completed. Total rows migrated: {total_rows_migrated}")
        
        # Close connections
        sqlite_conn.close()
        postgres_adapter.close()
        
        return True
    
    except Exception as e:
        logger.error(f"Error migrating data: {e}")
        return False

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Migrate data from SQLite to PostgreSQL')
    parser.add_argument('--sqlite-path', type=str, default='analysis_gdelt_chunks/gdelt_news.db',
                        help='Path to the SQLite database file')
    parser.add_argument('--config-path', type=str, default='config/database.json',
                        help='Path to database configuration file')
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
    args = parser.parse_args()
    
    # Get database configuration
    db_config = get_database_config(args.config_path)
    
    # Update configuration from command line arguments
    postgres_config = db_config['postgres'].copy()
    if args.postgres_host:
        postgres_config['host'] = args.postgres_host
    if args.postgres_port:
        postgres_config['port'] = args.postgres_port
    if args.postgres_db:
        postgres_config['dbname'] = args.postgres_db
    if args.postgres_user:
        postgres_config['user'] = args.postgres_user
    if args.postgres_password:
        postgres_config['password'] = args.postgres_password
    
    # Migrate data
    success = migrate_sqlite_to_postgres(args.sqlite_path, postgres_config)
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
