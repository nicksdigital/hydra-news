#!/usr/bin/env python3
"""
GDELT Database Migration

This script performs database migrations for the GDELT news database.
"""

import os
import sys
import argparse
import logging
import sqlite3

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='GDELT Database Migration')
    parser.add_argument('--db-path', type=str, required=True,
                        help='Path to the SQLite database file')
    parser.add_argument('--backup', action='store_true',
                        help='Create a backup of the database before migration')
    return parser.parse_args()

def create_backup(db_path):
    """Create a backup of the database"""
    import shutil
    from datetime import datetime
    
    # Create backup filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f"{db_path}.backup_{timestamp}"
    
    # Copy database file
    shutil.copy2(db_path, backup_path)
    
    logger.info(f"Created database backup at {backup_path}")
    
    return backup_path

def check_column_exists(conn, table, column):
    """Check if a column exists in a table"""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in cursor.fetchall()]
    return column in columns

def add_sentiment_polarity_column(conn):
    """Add sentiment_polarity column to articles table"""
    cursor = conn.cursor()
    
    # Check if column already exists
    if check_column_exists(conn, 'articles', 'sentiment_polarity'):
        logger.info("sentiment_polarity column already exists in articles table")
        return False
    
    # Add column
    cursor.execute("ALTER TABLE articles ADD COLUMN sentiment_polarity REAL")
    conn.commit()
    
    logger.info("Added sentiment_polarity column to articles table")
    return True

def add_trust_score_column(conn):
    """Add trust_score column to articles and entities tables"""
    cursor = conn.cursor()
    
    # Check if columns already exist
    articles_has_column = check_column_exists(conn, 'articles', 'trust_score')
    entities_has_column = check_column_exists(conn, 'entities', 'trust_score')
    
    if articles_has_column and entities_has_column:
        logger.info("trust_score columns already exist in articles and entities tables")
        return False
    
    # Add columns
    if not articles_has_column:
        cursor.execute("ALTER TABLE articles ADD COLUMN trust_score REAL DEFAULT 0.5")
        logger.info("Added trust_score column to articles table")
    
    if not entities_has_column:
        cursor.execute("ALTER TABLE entities ADD COLUMN trust_score REAL DEFAULT 0.5")
        logger.info("Added trust_score column to entities table")
    
    conn.commit()
    return True

def add_content_hash_column(conn):
    """Add content_hash column to articles table for deduplication"""
    cursor = conn.cursor()
    
    # Check if column already exists
    if check_column_exists(conn, 'articles', 'content_hash'):
        logger.info("content_hash column already exists in articles table")
        return False
    
    # Add column
    cursor.execute("ALTER TABLE articles ADD COLUMN content_hash TEXT")
    conn.commit()
    
    logger.info("Added content_hash column to articles table")
    
    # Create index on content_hash for faster deduplication
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_articles_content_hash ON articles(content_hash)')
    conn.commit()
    
    logger.info("Created index on content_hash column")
    
    return True

def add_fetch_date_column(conn):
    """Add fetch_date column to articles table"""
    cursor = conn.cursor()
    
    # Check if column already exists
    if check_column_exists(conn, 'articles', 'fetch_date'):
        logger.info("fetch_date column already exists in articles table")
        return False
    
    # Add column
    cursor.execute("ALTER TABLE articles ADD COLUMN fetch_date TEXT")
    conn.commit()
    
    logger.info("Added fetch_date column to articles table")
    return True

def main():
    """Main entry point"""
    args = parse_args()
    
    # Check if database file exists
    if not os.path.exists(args.db_path):
        logger.error(f"Database file not found: {args.db_path}")
        return 1
    
    # Create backup if requested
    if args.backup:
        create_backup(args.db_path)
    
    # Connect to database
    try:
        conn = sqlite3.connect(args.db_path)
        logger.info(f"Connected to database: {args.db_path}")
    except sqlite3.Error as e:
        logger.error(f"Error connecting to database: {e}")
        return 1
    
    try:
        # Perform migrations
        add_sentiment_polarity_column(conn)
        add_trust_score_column(conn)
        add_content_hash_column(conn)
        add_fetch_date_column(conn)
        
        logger.info("Database migration completed successfully")
    except sqlite3.Error as e:
        logger.error(f"Error during database migration: {e}")
        return 1
    finally:
        # Close database connection
        conn.close()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
