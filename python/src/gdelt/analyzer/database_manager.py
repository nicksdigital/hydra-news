#!/usr/bin/env python3
"""
GDELT Database Manager

This module provides functions for storing GDELT news data and extracted entities in a database.
"""

import os
import sqlite3
import pandas as pd
import json
import logging
from datetime import datetime

# Set up logging
logger = logging.getLogger(__name__)

class DatabaseManager:
    """Class for managing the GDELT database"""

    def __init__(self, db_path="gdelt_news.db"):
        """
        Initialize the database manager

        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self.conn = None
        self.cursor = None

    def connect(self):
        """Connect to the database"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            logger.info(f"Connected to database: {self.db_path}")
            return True
        except sqlite3.Error as e:
            logger.error(f"Error connecting to database: {e}")
            return False

    def close(self):
        """Close the database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Closed database connection")

    def create_tables(self):
        """Create the necessary tables if they don't exist"""
        try:
            # Create articles table
            self.cursor.execute('''
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
                trust_score REAL
            )
            ''')

            # Create entities table
            self.cursor.execute('''
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
            self.cursor.execute('''
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
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                domain TEXT UNIQUE,
                country TEXT,
                article_count INTEGER,
                trust_score REAL
            )
            ''')

            # Create themes table
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS themes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                theme_id TEXT UNIQUE,
                description TEXT,
                article_count INTEGER
            )
            ''')

            self.conn.commit()
            logger.info("Created database tables")
            return True
        except sqlite3.Error as e:
            logger.error(f"Error creating tables: {e}")
            return False

    def store_articles(self, articles_df):
        """
        Store articles in the database

        Args:
            articles_df: DataFrame containing articles

        Returns:
            Number of articles stored
        """
        if self.conn is None:
            logger.error("Database connection not established")
            return 0

        try:
            # Calculate initial trust scores
            if 'trust_score' not in articles_df.columns:
                articles_df['trust_score'] = self._calculate_article_trust_scores(articles_df)

            # Convert DataFrame to list of tuples
            articles_data = []
            for _, row in articles_df.iterrows():
                # Convert timestamp to string if needed
                seendate = row.get('seendate', '')
                if hasattr(seendate, 'strftime'):
                    seendate = seendate.strftime('%Y-%m-%d %H:%M:%S')

                article = (
                    row.get('url', ''),
                    row.get('title', ''),
                    seendate,
                    row.get('language', ''),
                    row.get('domain', ''),
                    row.get('sourcecountry', ''),
                    row.get('theme_id', ''),
                    row.get('theme_description', ''),
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    float(row.get('trust_score', 0.5))
                )
                articles_data.append(article)

            # Insert articles
            self.cursor.executemany('''
            INSERT OR IGNORE INTO articles
            (url, title, seendate, language, domain, sourcecountry, theme_id, theme_description, fetch_date, trust_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', articles_data)

            # Update source statistics
            self._update_source_stats(articles_df)

            # Update theme statistics
            self._update_theme_stats(articles_df)

            self.conn.commit()

            stored_count = self.cursor.rowcount
            logger.info(f"Stored {stored_count} articles in the database")
            return stored_count
        except sqlite3.Error as e:
            logger.error(f"Error storing articles: {e}")
            self.conn.rollback()
            return 0

    def store_entities(self, entities_df, entity_stats_df):
        """
        Store entities and their relationships with articles in the database

        Args:
            entities_df: DataFrame containing entity mentions in articles
            entity_stats_df: DataFrame containing entity statistics

        Returns:
            Number of entities stored
        """
        if self.conn is None:
            logger.error("Database connection not established")
            return 0

        try:
            # Calculate trust scores for entities
            if 'trust_score' not in entity_stats_df.columns:
                entity_stats_df['trust_score'] = self._calculate_entity_trust_scores(entity_stats_df)

            # Store entities
            entities_data = []
            for _, row in entity_stats_df.iterrows():
                entity = (
                    row['entity'],
                    row['type'],
                    row['count'],
                    row['num_sources'],
                    row['source_diversity'],
                    row['trust_score']
                )
                entities_data.append(entity)

            # Insert entities
            self.cursor.executemany('''
            INSERT OR REPLACE INTO entities
            (text, type, count, num_sources, source_diversity, trust_score)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', entities_data)

            # Get entity IDs
            entity_ids = {}
            self.cursor.execute('SELECT id, text FROM entities')
            for entity_id, entity_text in self.cursor.fetchall():
                entity_ids[entity_text] = entity_id

            # Store article-entity relationships
            if not entities_df.empty:
                # Get article IDs
                article_ids = {}
                self.cursor.execute('SELECT id, url FROM articles')
                for article_id, url in self.cursor.fetchall():
                    article_ids[url] = article_id

                # Prepare article-entity data
                article_entity_data = []
                for _, row in entities_df.iterrows():
                    article_url = row['article_url']
                    entity_text = row['text']

                    if article_url in article_ids and entity_text in entity_ids:
                        article_id = article_ids[article_url]
                        entity_id = entity_ids[entity_text]

                        # Create context JSON
                        context = {
                            'start': int(row.get('start', 0)),
                            'end': int(row.get('end', 0)),
                            'method': row.get('method', 'unknown')
                        }

                        article_entity_data.append((
                            article_id,
                            entity_id,
                            json.dumps(context)
                        ))

                # Insert article-entity relationships
                self.cursor.executemany('''
                INSERT OR IGNORE INTO article_entities
                (article_id, entity_id, context)
                VALUES (?, ?, ?)
                ''', article_entity_data)

            self.conn.commit()

            stored_count = len(entities_data)
            logger.info(f"Stored {stored_count} entities in the database")
            return stored_count
        except sqlite3.Error as e:
            logger.error(f"Error storing entities: {e}")
            self.conn.rollback()
            return 0

    def _update_source_stats(self, articles_df):
        """Update source statistics in the database"""
        try:
            # Count articles by domain
            domain_counts = articles_df['domain'].value_counts().reset_index()
            domain_counts.columns = ['domain', 'article_count']

            # Get countries for domains
            domain_countries = articles_df.groupby('domain')['sourcecountry'].first().reset_index()

            # Merge counts and countries
            domain_stats = pd.merge(domain_counts, domain_countries, on='domain')

            # Calculate trust scores for sources
            domain_stats['trust_score'] = self._calculate_source_trust_scores(domain_stats, articles_df)

            # Convert to list of tuples
            source_data = []
            for _, row in domain_stats.iterrows():
                source = (
                    row['domain'],
                    row['sourcecountry'],
                    row['article_count'],
                    row['trust_score']
                )
                source_data.append(source)

            # Insert or update sources
            self.cursor.executemany('''
            INSERT OR REPLACE INTO sources
            (domain, country, article_count, trust_score)
            VALUES (?, ?, ?, ?)
            ''', source_data)

            logger.info(f"Updated statistics for {len(source_data)} sources")
        except Exception as e:
            logger.error(f"Error updating source statistics: {e}")

    def _update_theme_stats(self, articles_df):
        """Update theme statistics in the database"""
        try:
            # Count articles by theme
            theme_counts = articles_df['theme_id'].value_counts().reset_index()
            theme_counts.columns = ['theme_id', 'article_count']

            # Get descriptions for themes
            theme_descriptions = articles_df.groupby('theme_id')['theme_description'].first().reset_index()

            # Merge counts and descriptions
            theme_stats = pd.merge(theme_counts, theme_descriptions, on='theme_id')

            # Convert to list of tuples
            theme_data = []
            for _, row in theme_stats.iterrows():
                theme = (
                    row['theme_id'],
                    row['theme_description'],
                    row['article_count']
                )
                theme_data.append(theme)

            # Insert or update themes
            self.cursor.executemany('''
            INSERT OR REPLACE INTO themes
            (theme_id, description, article_count)
            VALUES (?, ?, ?)
            ''', theme_data)

            logger.info(f"Updated statistics for {len(theme_data)} themes")
        except Exception as e:
            logger.error(f"Error updating theme statistics: {e}")

    def _calculate_article_trust_scores(self, articles_df):
        """
        Calculate trust scores for articles

        This is a simple implementation that can be enhanced with more sophisticated algorithms.

        Args:
            articles_df: DataFrame containing articles

        Returns:
            Series with trust scores
        """
        # Initialize with base score
        trust_scores = pd.Series(0.5, index=articles_df.index)

        try:
            # 1. Adjust based on domain reputation (if available in database)
            if self.conn is not None:
                domain_scores = {}
                self.cursor.execute('SELECT domain, trust_score FROM sources')
                for domain, score in self.cursor.fetchall():
                    domain_scores[domain] = score

                # Apply domain scores
                for idx, row in articles_df.iterrows():
                    domain = row.get('domain', '')
                    if domain in domain_scores:
                        trust_scores[idx] = domain_scores[domain]

            # 2. Adjust based on source country (some countries might have more reliable media)
            # This is a simplified example - in reality, you would want a more nuanced approach
            country_factors = {
                'US': 0.1,
                'GB': 0.1,
                'CA': 0.1,
                'AU': 0.1,
                'FR': 0.1,
                'DE': 0.1
            }

            for idx, row in articles_df.iterrows():
                country = row.get('sourcecountry', '')
                if country in country_factors:
                    trust_scores[idx] += country_factors[country]

            # 3. Cap scores between 0.1 and 0.9
            trust_scores = trust_scores.clip(0.1, 0.9)

            return trust_scores
        except Exception as e:
            logger.error(f"Error calculating article trust scores: {e}")
            return pd.Series(0.5, index=articles_df.index)

    def _calculate_entity_trust_scores(self, entity_stats_df):
        """
        Calculate trust scores for entities

        Args:
            entity_stats_df: DataFrame containing entity statistics

        Returns:
            Series with trust scores
        """
        # Initialize with base score
        trust_scores = pd.Series(0.5, index=entity_stats_df.index)

        try:
            # 1. Adjust based on source diversity
            trust_scores += entity_stats_df['source_diversity'] * 0.2

            # 2. Adjust based on mention count (more mentions = higher trust)
            # Normalize counts to 0-1 range
            max_count = entity_stats_df['count'].max()
            if max_count > 0:
                normalized_counts = entity_stats_df['count'] / max_count
                trust_scores += normalized_counts * 0.2

            # 3. Cap scores between 0.1 and 0.9
            trust_scores = trust_scores.clip(0.1, 0.9)

            return trust_scores
        except Exception as e:
            logger.error(f"Error calculating entity trust scores: {e}")
            return pd.Series(0.5, index=entity_stats_df.index)

    def _calculate_source_trust_scores(self, domain_stats, articles_df):
        """
        Calculate trust scores for sources

        Args:
            domain_stats: DataFrame containing domain statistics
            articles_df: DataFrame containing articles

        Returns:
            Series with trust scores
        """
        # Initialize with base score
        trust_scores = pd.Series(0.5, index=domain_stats.index)

        try:
            # 1. Adjust based on article count (more articles = more established source)
            max_count = domain_stats['article_count'].max()
            if max_count > 0:
                normalized_counts = domain_stats['article_count'] / max_count
                trust_scores += normalized_counts * 0.1

            # 2. Adjust based on country (some countries might have more reliable media)
            country_factors = {
                'US': 0.1,
                'GB': 0.1,
                'CA': 0.1,
                'AU': 0.1,
                'FR': 0.1,
                'DE': 0.1
            }

            for idx, row in domain_stats.iterrows():
                country = row.get('sourcecountry', '')
                if country in country_factors:
                    trust_scores[idx] += country_factors[country]

            # 3. Cap scores between 0.1 and 0.9
            trust_scores = trust_scores.clip(0.1, 0.9)

            return trust_scores
        except Exception as e:
            logger.error(f"Error calculating source trust scores: {e}")
            return pd.Series(0.5, index=domain_stats.index)

    def get_articles(self, limit=100, theme=None, min_trust_score=None):
        """
        Get articles from the database

        Args:
            limit: Maximum number of articles to return
            theme: Filter by theme ID
            min_trust_score: Minimum trust score

        Returns:
            DataFrame with articles
        """
        if self.conn is None:
            logger.error("Database connection not established")
            return pd.DataFrame()

        try:
            # Build query
            query = 'SELECT * FROM articles'
            params = []

            # Add filters
            filters = []
            if theme:
                filters.append('theme_id = ?')
                params.append(theme)

            if min_trust_score is not None:
                filters.append('trust_score >= ?')
                params.append(min_trust_score)

            if filters:
                query += ' WHERE ' + ' AND '.join(filters)

            # Add limit
            query += ' ORDER BY seendate DESC LIMIT ?'
            params.append(limit)

            # Execute query
            df = pd.read_sql_query(query, self.conn, params=params)

            logger.info(f"Retrieved {len(df)} articles from the database")
            return df
        except sqlite3.Error as e:
            logger.error(f"Error retrieving articles: {e}")
            return pd.DataFrame()

    def get_entities(self, limit=100, entity_type=None, min_trust_score=None):
        """
        Get entities from the database

        Args:
            limit: Maximum number of entities to return
            entity_type: Filter by entity type
            min_trust_score: Minimum trust score

        Returns:
            DataFrame with entities
        """
        if self.conn is None:
            logger.error("Database connection not established")
            return pd.DataFrame()

        try:
            # Build query
            query = 'SELECT * FROM entities'
            params = []

            # Add filters
            filters = []
            if entity_type:
                filters.append('type = ?')
                params.append(entity_type)

            if min_trust_score is not None:
                filters.append('trust_score >= ?')
                params.append(min_trust_score)

            if filters:
                query += ' WHERE ' + ' AND '.join(filters)

            # Add limit
            query += ' ORDER BY count DESC LIMIT ?'
            params.append(limit)

            # Execute query
            df = pd.read_sql_query(query, self.conn, params=params)

            logger.info(f"Retrieved {len(df)} entities from the database")
            return df
        except sqlite3.Error as e:
            logger.error(f"Error retrieving entities: {e}")
            return pd.DataFrame()

    def get_entity_articles(self, entity_id, limit=100):
        """
        Get articles mentioning a specific entity

        Args:
            entity_id: ID of the entity
            limit: Maximum number of articles to return

        Returns:
            DataFrame with articles
        """
        if self.conn is None:
            logger.error("Database connection not established")
            return pd.DataFrame()

        try:
            # Build query
            query = '''
            SELECT a.* FROM articles a
            JOIN article_entities ae ON a.id = ae.article_id
            WHERE ae.entity_id = ?
            ORDER BY a.seendate DESC
            LIMIT ?
            '''

            # Execute query
            df = pd.read_sql_query(query, self.conn, params=[entity_id, limit])

            logger.info(f"Retrieved {len(df)} articles for entity ID {entity_id}")
            return df
        except sqlite3.Error as e:
            logger.error(f"Error retrieving entity articles: {e}")
            return pd.DataFrame()

    def get_article_entities(self, article_id):
        """
        Get entities mentioned in a specific article

        Args:
            article_id: ID of the article

        Returns:
            DataFrame with entities
        """
        if self.conn is None:
            logger.error("Database connection not established")
            return pd.DataFrame()

        try:
            # Build query
            query = '''
            SELECT e.*, ae.context FROM entities e
            JOIN article_entities ae ON e.id = ae.entity_id
            WHERE ae.article_id = ?
            ORDER BY e.count DESC
            '''

            # Execute query
            df = pd.read_sql_query(query, self.conn, params=[article_id])

            logger.info(f"Retrieved {len(df)} entities for article ID {article_id}")
            return df
        except sqlite3.Error as e:
            logger.error(f"Error retrieving article entities: {e}")
            return pd.DataFrame()

    def get_source_stats(self, limit=100):
        """
        Get source statistics

        Args:
            limit: Maximum number of sources to return

        Returns:
            DataFrame with source statistics
        """
        if self.conn is None:
            logger.error("Database connection not established")
            return pd.DataFrame()

        try:
            # Build query
            query = '''
            SELECT * FROM sources
            ORDER BY article_count DESC
            LIMIT ?
            '''

            # Execute query
            df = pd.read_sql_query(query, self.conn, params=[limit])

            logger.info(f"Retrieved statistics for {len(df)} sources")
            return df
        except sqlite3.Error as e:
            logger.error(f"Error retrieving source statistics: {e}")
            return pd.DataFrame()

    def get_theme_stats(self):
        """
        Get theme statistics

        Returns:
            DataFrame with theme statistics
        """
        if self.conn is None:
            logger.error("Database connection not established")
            return pd.DataFrame()

        try:
            # Build query
            query = '''
            SELECT * FROM themes
            ORDER BY article_count DESC
            '''

            # Execute query
            df = pd.read_sql_query(query, self.conn)

            logger.info(f"Retrieved statistics for {len(df)} themes")
            return df
        except sqlite3.Error as e:
            logger.error(f"Error retrieving theme statistics: {e}")
            return pd.DataFrame()

    def get_database_summary(self):
        """
        Get a summary of the database contents

        Returns:
            Dictionary with database summary
        """
        if self.conn is None:
            logger.error("Database connection not established")
            return {}

        try:
            summary = {}

            # Count articles
            self.cursor.execute('SELECT COUNT(*) FROM articles')
            summary['article_count'] = self.cursor.fetchone()[0]

            # Count entities
            self.cursor.execute('SELECT COUNT(*) FROM entities')
            summary['entity_count'] = self.cursor.fetchone()[0]

            # Count sources
            self.cursor.execute('SELECT COUNT(*) FROM sources')
            summary['source_count'] = self.cursor.fetchone()[0]

            # Count themes
            self.cursor.execute('SELECT COUNT(*) FROM themes')
            summary['theme_count'] = self.cursor.fetchone()[0]

            # Get date range
            self.cursor.execute('SELECT MIN(seendate), MAX(seendate) FROM articles')
            min_date, max_date = self.cursor.fetchone()
            summary['date_range'] = {
                'start_date': min_date,
                'end_date': max_date
            }

            # Get language counts
            self.cursor.execute('SELECT language, COUNT(*) FROM articles GROUP BY language')
            summary['languages'] = {lang: count for lang, count in self.cursor.fetchall()}

            # Get entity type counts
            self.cursor.execute('SELECT type, COUNT(*) FROM entities GROUP BY type')
            summary['entity_types'] = {type_: count for type_, count in self.cursor.fetchall()}

            # Get average trust scores
            self.cursor.execute('SELECT AVG(trust_score) FROM articles')
            summary['avg_article_trust'] = self.cursor.fetchone()[0]

            self.cursor.execute('SELECT AVG(trust_score) FROM entities')
            summary['avg_entity_trust'] = self.cursor.fetchone()[0]

            self.cursor.execute('SELECT AVG(trust_score) FROM sources')
            summary['avg_source_trust'] = self.cursor.fetchone()[0]

            logger.info("Generated database summary")
            return summary
        except sqlite3.Error as e:
            logger.error(f"Error generating database summary: {e}")
            return {}
