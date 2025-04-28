#!/usr/bin/env python3
"""
Reset the database and recreate it with the correct schema
"""

import os
import sqlite3
import logging
import argparse

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def reset_database(db_path):
    """
    Reset the database and recreate it with the correct schema

    Args:
        db_path: Path to the database file
    """
    # Remove the database file if it exists
    if os.path.exists(db_path):
        logger.info(f"Removing existing database: {db_path}")
        os.remove(db_path)

    # Create the database directory if it doesn't exist
    db_dir = os.path.dirname(db_path)
    if not os.path.exists(db_dir):
        logger.info(f"Creating database directory: {db_dir}")
        os.makedirs(db_dir)

    # Connect to the database
    logger.info(f"Creating new database: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create tables
    logger.info("Creating tables")

    # Table for tracking processed chunks
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS processed_chunks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chunk_name TEXT UNIQUE,
        chunk_path TEXT,
        processed_date TEXT,
        num_articles INTEGER DEFAULT 0,
        status TEXT
    )
    ''')

    # Table for articles
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS articles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT UNIQUE,
        title TEXT,
        title_translated TEXT,
        seendate TEXT,
        language TEXT,
        domain TEXT,
        sourcecountry TEXT,
        theme_id TEXT,
        theme_description TEXT,
        fetch_date TEXT,
        trust_score REAL DEFAULT 0.5,
        sentiment_polarity REAL DEFAULT 0.0,
        content_hash TEXT
    )
    ''')

    # Table for entities
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS entities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        text TEXT,
        type TEXT,
        count INTEGER DEFAULT 0,
        num_sources INTEGER DEFAULT 0,
        source_diversity REAL DEFAULT 0.0,
        trust_score REAL DEFAULT 0.5,
        UNIQUE(text, type)
    )
    ''')

    # Table for article-entity relationships
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS article_entities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        article_id INTEGER,
        entity_id INTEGER,
        context TEXT,
        UNIQUE(article_id, entity_id),
        FOREIGN KEY (article_id) REFERENCES articles(id),
        FOREIGN KEY (entity_id) REFERENCES entities(id)
    )
    ''')

    # Table for sources
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sources (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        domain TEXT UNIQUE,
        country TEXT,
        article_count INTEGER DEFAULT 0,
        trust_score REAL DEFAULT 0.5
    )
    ''')

    # Table for themes
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS themes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        theme_id TEXT UNIQUE,
        description TEXT,
        article_count INTEGER DEFAULT 0
    )
    ''')

    # Commit changes and close connection
    conn.commit()
    conn.close()

    logger.info("Database reset and recreated successfully")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Reset database and recreate schema')
    parser.add_argument('--db-path', type=str, default='analysis_gdelt_chunks/gdelt_news.db',
                        help='Path to the database file')
    args = parser.parse_args()

    reset_database(args.db_path)

if __name__ == '__main__':
    main()
