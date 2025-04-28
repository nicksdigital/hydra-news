#!/usr/bin/env python3
"""
Create a new database schema for chunk-based processing
"""

import os
import sqlite3
import logging
import argparse
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_database(db_path):
    """Create a new database with the necessary tables"""
    logger.info(f"Creating database at {db_path}")
    
    # Create database directory if it doesn't exist
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create articles table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS articles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT UNIQUE,
        title TEXT,
        seendate TEXT,
        language TEXT,
        domain TEXT,
        sourcecountry TEXT,
        theme_id TEXT,
        theme_description TEXT,
        fetch_date TEXT,
        trust_score REAL,
        sentiment_polarity REAL,
        content_hash TEXT
    )
    ''')
    
    # Create entities table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS entities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        text TEXT,
        type TEXT,
        count INTEGER,
        num_sources INTEGER,
        source_diversity REAL,
        trust_score REAL
    )
    ''')
    
    # Create article_entities table (for many-to-many relationship)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS article_entities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        article_id INTEGER,
        entity_id INTEGER,
        context TEXT,
        FOREIGN KEY (article_id) REFERENCES articles (id),
        FOREIGN KEY (entity_id) REFERENCES entities (id)
    )
    ''')
    
    # Create sources table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sources (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        domain TEXT UNIQUE,
        country TEXT,
        article_count INTEGER,
        trust_score REAL
    )
    ''')
    
    # Create themes table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS themes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        theme_id TEXT UNIQUE,
        description TEXT,
        article_count INTEGER
    )
    ''')
    
    # Create processed_chunks table to track which chunks have been processed
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS processed_chunks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chunk_name TEXT UNIQUE,
        chunk_path TEXT,
        num_articles INTEGER,
        processed_date TEXT,
        status TEXT
    )
    ''')
    
    # Create indexes for performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_articles_content_hash ON articles(content_hash)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_entities_text ON entities(text)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_article_entities_article_id ON article_entities(article_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_article_entities_entity_id ON article_entities(entity_id)')
    
    # Commit changes and close connection
    conn.commit()
    conn.close()
    
    logger.info("Database created successfully")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Create a new database for chunk-based processing')
    parser.add_argument('--db-path', type=str, default='analysis_gdelt_chunks/gdelt_news.db',
                        help='Path to the database file')
    args = parser.parse_args()
    
    create_database(args.db_path)

if __name__ == '__main__':
    main()
