#!/usr/bin/env python3
"""
PostgreSQL Database Adapter for GDELT News Analysis

This module provides a PostgreSQL database adapter for the GDELT News Analysis system.
"""

import os
import logging
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
import time

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PostgresAdapter:
    """PostgreSQL database adapter for GDELT News Analysis"""

    def __init__(self, host='localhost', port=5432, dbname='gdelt_news',
                 user='postgres', password='postgres', min_conn=1, max_conn=10):
        """
        Initialize the PostgreSQL adapter

        Args:
            host: Database host
            port: Database port
            dbname: Database name
            user: Database user
            password: Database password
            min_conn: Minimum number of connections in the pool
            max_conn: Maximum number of connections in the pool
        """
        self.connection_params = {
            'host': host,
            'port': port,
            'dbname': dbname,
            'user': user,
            'password': password
        }

        self.min_conn = min_conn
        self.max_conn = max_conn
        self.connection_pool = None

        # Initialize connection pool
        self._initialize_connection_pool()

    def _initialize_connection_pool(self):
        """Initialize the connection pool"""
        try:
            self.connection_pool = psycopg2.pool.ThreadedConnectionPool(
                self.min_conn,
                self.max_conn,
                **self.connection_params
            )
            logger.info(f"Initialized PostgreSQL connection pool with {self.min_conn}-{self.max_conn} connections")
        except Exception as e:
            logger.error(f"Error initializing PostgreSQL connection pool: {e}")
            raise

    def get_connection(self, retries=3, retry_delay=2):
        """
        Get a connection from the pool with retry logic

        Args:
            retries: Number of retries if getting a connection fails
            retry_delay: Delay in seconds between retries

        Returns:
            PostgreSQL connection object
        """
        for attempt in range(retries):
            try:
                conn = self.connection_pool.getconn()
                # Set cursor factory to return dictionaries
                conn.cursor_factory = RealDictCursor
                return conn
            except (psycopg2.OperationalError, psycopg2.pool.PoolError) as e:
                if attempt < retries - 1:
                    logger.warning(f"Error getting connection from pool, retrying in {retry_delay} seconds (attempt {attempt + 1}/{retries}): {e}")
                    time.sleep(retry_delay)
                else:
                    logger.error(f"Failed to get connection after {retries} attempts: {e}")
                    raise

    def release_connection(self, conn):
        """
        Release a connection back to the pool

        Args:
            conn: PostgreSQL connection object
        """
        try:
            self.connection_pool.putconn(conn)
        except Exception as e:
            logger.error(f"Error releasing connection back to pool: {e}")

    def execute_query(self, query, params=None, fetch=True, retries=3, retry_delay=2):
        """
        Execute a query with retry logic

        Args:
            query: SQL query to execute
            params: Query parameters
            fetch: Whether to fetch results
            retries: Number of retries if query fails
            retry_delay: Delay in seconds between retries

        Returns:
            Query results if fetch is True, otherwise None
        """
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            for attempt in range(retries):
                try:
                    cursor.execute(query, params)

                    # Always commit the transaction
                    conn.commit()

                    if fetch:
                        results = cursor.fetchall()
                        return results
                    else:
                        return None

                except psycopg2.OperationalError as e:
                    if attempt < retries - 1:
                        logger.warning(f"Database error, retrying in {retry_delay} seconds (attempt {attempt + 1}/{retries}): {e}")
                        time.sleep(retry_delay)
                        # Get a new connection
                        self.release_connection(conn)
                        conn = self.get_connection()
                        cursor = conn.cursor()
                    else:
                        logger.error(f"Failed to execute query after {retries} attempts: {e}")
                        raise

        finally:
            if conn:
                self.release_connection(conn)

    def execute_transaction(self, queries, retries=3, retry_delay=2):
        """
        Execute multiple queries in a transaction with retry logic

        Args:
            queries: List of (query, params) tuples
            retries: Number of retries if transaction fails
            retry_delay: Delay in seconds between retries

        Returns:
            True if transaction succeeded, False otherwise
        """
        conn = None
        try:
            conn = self.get_connection()

            for attempt in range(retries):
                try:
                    cursor = conn.cursor()

                    # Execute all queries in a transaction
                    for query, params in queries:
                        cursor.execute(query, params)

                    # Commit the transaction
                    conn.commit()
                    return True

                except psycopg2.Error as e:
                    # Rollback the transaction
                    conn.rollback()

                    if attempt < retries - 1:
                        logger.warning(f"Transaction failed, retrying in {retry_delay} seconds (attempt {attempt + 1}/{retries}): {e}")
                        time.sleep(retry_delay)
                    else:
                        logger.error(f"Failed to execute transaction after {retries} attempts: {e}")
                        return False

        finally:
            if conn:
                self.release_connection(conn)

    def create_tables(self):
        """Create database tables"""
        # Define table creation queries
        queries = [
            # Chunks table
            ("""
            CREATE TABLE IF NOT EXISTS chunks (
                id SERIAL PRIMARY KEY,
                name TEXT UNIQUE,
                path TEXT,
                processed_date TIMESTAMP,
                status TEXT
            )
            """, None),

            # Articles table
            ("""
            CREATE TABLE IF NOT EXISTS articles (
                id SERIAL PRIMARY KEY,
                url TEXT UNIQUE,
                title TEXT,
                title_translated TEXT,
                seendate TIMESTAMP,
                language TEXT,
                domain TEXT,
                sourcecountry TEXT,
                theme_id TEXT,
                theme_description TEXT,
                fetch_date TIMESTAMP,
                trust_score REAL DEFAULT 0.5,
                sentiment_polarity REAL DEFAULT 0.0,
                content_hash TEXT
            )
            """, None),

            # Entities table
            ("""
            CREATE TABLE IF NOT EXISTS entities (
                id SERIAL PRIMARY KEY,
                text TEXT,
                type TEXT,
                count INTEGER DEFAULT 0,
                num_sources INTEGER DEFAULT 0,
                source_diversity REAL DEFAULT 0.0,
                trust_score REAL DEFAULT 0.5,
                UNIQUE(text, type)
            )
            """, None),

            # Article-Entity relationship table
            ("""
            CREATE TABLE IF NOT EXISTS article_entities (
                id SERIAL PRIMARY KEY,
                article_id INTEGER REFERENCES articles(id) ON DELETE CASCADE,
                entity_id INTEGER REFERENCES entities(id) ON DELETE CASCADE,
                context TEXT,
                start_pos INTEGER,
                end_pos INTEGER,
                UNIQUE(article_id, entity_id)
            )
            """, None),

            # Sources table
            ("""
            CREATE TABLE IF NOT EXISTS sources (
                id SERIAL PRIMARY KEY,
                domain TEXT UNIQUE,
                country TEXT,
                article_count INTEGER DEFAULT 0,
                trust_score REAL DEFAULT 0.5
            )
            """, None),

            # Create indexes for better performance
            ("""
            CREATE INDEX IF NOT EXISTS idx_articles_seendate ON articles(seendate)
            """, None),

            ("""
            CREATE INDEX IF NOT EXISTS idx_articles_language ON articles(language)
            """, None),

            ("""
            CREATE INDEX IF NOT EXISTS idx_articles_domain ON articles(domain)
            """, None),

            ("""
            CREATE INDEX IF NOT EXISTS idx_articles_theme_id ON articles(theme_id)
            """, None),

            ("""
            CREATE INDEX IF NOT EXISTS idx_entities_text ON entities(text)
            """, None),

            ("""
            CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(type)
            """, None),

            ("""
            CREATE INDEX IF NOT EXISTS idx_article_entities_article_id ON article_entities(article_id)
            """, None),

            ("""
            CREATE INDEX IF NOT EXISTS idx_article_entities_entity_id ON article_entities(entity_id)
            """, None)
        ]

        # Execute all queries in a transaction
        success = self.execute_transaction(queries)

        if success:
            logger.info("Created database tables successfully")
        else:
            logger.error("Failed to create database tables")

    def reset_database(self):
        """Reset the database by dropping and recreating all tables"""
        # Define table drop queries
        queries = [
            ("""
            DROP TABLE IF EXISTS article_entities CASCADE
            """, None),

            ("""
            DROP TABLE IF EXISTS entities CASCADE
            """, None),

            ("""
            DROP TABLE IF EXISTS articles CASCADE
            """, None),

            ("""
            DROP TABLE IF EXISTS sources CASCADE
            """, None),

            ("""
            DROP TABLE IF EXISTS chunks CASCADE
            """, None)
        ]

        # Execute all queries in a transaction
        success = self.execute_transaction(queries)

        if success:
            logger.info("Dropped all tables successfully")
            # Create tables
            self.create_tables()
        else:
            logger.error("Failed to drop tables")

    def close(self):
        """Close the connection pool"""
        if self.connection_pool:
            self.connection_pool.closeall()
            logger.info("Closed PostgreSQL connection pool")

# Singleton instance
_postgres_adapter = None

def get_postgres_adapter(host='localhost', port=5432, dbname='gdelt_news',
                         user='postgres', password='postgres', min_conn=1, max_conn=10):
    """
    Get the PostgreSQL adapter singleton instance

    Args:
        host: Database host
        port: Database port
        dbname: Database name
        user: Database user
        password: Database password
        min_conn: Minimum number of connections in the pool
        max_conn: Maximum number of connections in the pool

    Returns:
        PostgreSQL adapter instance
    """
    global _postgres_adapter

    if _postgres_adapter is None:
        _postgres_adapter = PostgresAdapter(
            host=host,
            port=port,
            dbname=dbname,
            user=user,
            password=password,
            min_conn=min_conn,
            max_conn=max_conn
        )

    return _postgres_adapter

def main():
    """Main function for command-line interface"""
    import argparse

    parser = argparse.ArgumentParser(description='PostgreSQL adapter for GDELT News Analysis')
    parser.add_argument('--host', type=str, default='localhost',
                        help='PostgreSQL host')
    parser.add_argument('--port', type=int, default=5432,
                        help='PostgreSQL port')
    parser.add_argument('--dbname', type=str, default='gdelt_news',
                        help='PostgreSQL database name')
    parser.add_argument('--user', type=str, default='postgres',
                        help='PostgreSQL user')
    parser.add_argument('--password', type=str, default='postgres',
                        help='PostgreSQL password')
    parser.add_argument('--min-conn', type=int, default=1,
                        help='Minimum number of connections in the pool')
    parser.add_argument('--max-conn', type=int, default=10,
                        help='Maximum number of connections in the pool')
    parser.add_argument('--reset', action='store_true',
                        help='Reset the database')
    parser.add_argument('--create-tables', action='store_true',
                        help='Create database tables')
    args = parser.parse_args()

    # Get PostgreSQL adapter
    adapter = get_postgres_adapter(
        host=args.host,
        port=args.port,
        dbname=args.dbname,
        user=args.user,
        password=args.password,
        min_conn=args.min_conn,
        max_conn=args.max_conn
    )

    # Perform actions
    if args.reset:
        logger.info(f"Resetting database: {args.dbname}")
        adapter.reset_database()
    elif args.create_tables:
        logger.info(f"Creating tables in database: {args.dbname}")
        adapter.create_tables()

    # Close adapter
    adapter.close()

if __name__ == '__main__':
    main()
