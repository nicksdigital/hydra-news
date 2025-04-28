#!/usr/bin/env python3
"""
Process a single chunk of GDELT data
"""

import os
import sys
import pandas as pd
import logging
import argparse
import time
from datetime import datetime
from python.src.gdelt.analyzer.simple_entity_extractor import SimpleEntityExtractor
from python.src.gdelt.analyzer.sentiment_analyzer import SentimentAnalyzer
from python.src.gdelt.analyzer.translator import ArticleTranslator
from python.src.gdelt.database.postgres_adapter import get_postgres_adapter
from python.src.gdelt.config.database_config import get_database_config

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def process_chunk(chunk_path, db_config=None, output_dir=None, use_postgres=True):
    """
    Process a single chunk of GDELT data

    Args:
        chunk_path: Path to the chunk CSV file
        db_config: Database configuration (dict or path to SQLite DB)
        output_dir: Directory to save output files
        use_postgres: Whether to use PostgreSQL (True) or SQLite (False)

    Returns:
        True if successful, False otherwise
    """
    logger.info(f"Processing chunk: {chunk_path}")

    # Extract chunk name from path
    chunk_name = os.path.basename(chunk_path)

    # Connect to database
    try:
        if use_postgres:
            # Use PostgreSQL
            if isinstance(db_config, dict):
                # Use provided configuration
                db = get_postgres_adapter(**db_config)
            else:
                # Use default configuration
                db = get_postgres_adapter()

            # Check if chunk has already been processed
            result = db.execute_query(
                'SELECT status FROM chunks WHERE name = %s',
                (chunk_name,)
            )

            if result and result[0]['status'] == 'completed':
                logger.info(f"Chunk {chunk_name} has already been processed. Skipping.")
                return True

            # Mark chunk as processing
            processed_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            db.execute_query(
                '''
                INSERT INTO chunks (name, path, processed_date, status)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (name) DO UPDATE
                SET path = EXCLUDED.path,
                    processed_date = EXCLUDED.processed_date,
                    status = EXCLUDED.status
                ''',
                (chunk_name, chunk_path, processed_date, 'processing'),
                fetch=False
            )
        else:
            # Use SQLite
            db_path = db_config if isinstance(db_config, str) else 'analysis_gdelt_chunks/gdelt_news.db'
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Check if chunk has already been processed
            cursor.execute('SELECT status FROM processed_chunks WHERE chunk_name = ?', (chunk_name,))
            result = cursor.fetchone()
            if result and result[0] == 'completed':
                logger.info(f"Chunk {chunk_name} has already been processed. Skipping.")
                conn.close()
                return True

            # Mark chunk as processing
            processed_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute('''
            INSERT OR REPLACE INTO processed_chunks
            (chunk_name, chunk_path, processed_date, status)
            VALUES (?, ?, ?, ?)
            ''', (chunk_name, chunk_path, processed_date, 'processing'))
            conn.commit()

        # Load chunk data
        try:
            articles_df = pd.read_csv(chunk_path)
            logger.info(f"Loaded {len(articles_df)} articles from {chunk_path}")
        except Exception as e:
            logger.error(f"Error loading chunk data: {e}")
            cursor.execute('UPDATE processed_chunks SET status = ? WHERE chunk_name = ?',
                          ('error', chunk_name))
            conn.commit()
            conn.close()
            return False

        # Process articles
        try:
            # Initialize processors
            entity_extractor = SimpleEntityExtractor()
            sentiment_analyzer = SentimentAnalyzer()
            translator = ArticleTranslator(cache_dir=os.path.join(output_dir, 'translation_cache'))

            # Translate non-English articles
            non_english_count = len(articles_df[articles_df['language'] != 'en'])
            if non_english_count > 0:
                logger.info(f"Translating {non_english_count} non-English articles")
                articles_df = translator.translate_dataframe(articles_df,
                                                           language_column='language',
                                                           text_columns=['title'])
                logger.info("Translation completed")

                # Use translated titles for entity extraction and sentiment analysis
                # Create a copy of the dataframe with translated titles
                processing_df = articles_df.copy()
                for idx, row in processing_df.iterrows():
                    if 'title_translated' in row and row['title_translated'] is not None:
                        processing_df.at[idx, 'title'] = row['title_translated']
            else:
                processing_df = articles_df

            # Extract entities (using translated text for non-English articles)
            entities_df = entity_extractor.extract_entities_from_dataframe(processing_df)
            logger.info(f"Extracted {len(entities_df)} entity mentions")

            # Calculate entity statistics
            entity_stats_df = entity_extractor.calculate_entity_stats()
            logger.info(f"Calculated statistics for {len(entity_stats_df)} entities")

            # Analyze sentiment (using translated text for non-English articles)
            articles_df = sentiment_analyzer.analyze_dataframe(processing_df)
            logger.info("Analyzed sentiment for articles")

            # Restore original titles but keep translations
            if non_english_count > 0:
                for col in ['sentiment_polarity', 'sentiment_positive', 'sentiment_negative']:
                    if col in processing_df.columns:
                        articles_df[col] = processing_df[col]

            # Store data in database
            store_data_in_db(conn, articles_df, entities_df, entity_stats_df)

            # Update chunk status
            cursor.execute('''
            UPDATE processed_chunks
            SET num_articles = ?, status = ?
            WHERE chunk_name = ?
            ''', (len(articles_df), 'completed', chunk_name))
            conn.commit()

            # Save output files if requested
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
                chunk_output_dir = os.path.join(output_dir, os.path.splitext(chunk_name)[0])
                os.makedirs(chunk_output_dir, exist_ok=True)

                # Save entities
                entities_path = os.path.join(chunk_output_dir, "entities.csv")
                entities_df.to_csv(entities_path, index=False)

                # Save entity stats
                entity_stats_path = os.path.join(chunk_output_dir, "entity_stats.csv")
                entity_stats_df.to_csv(entity_stats_path, index=False)

                logger.info(f"Saved output files to {chunk_output_dir}")

            logger.info(f"Successfully processed chunk: {chunk_name}")
            return True

        except Exception as e:
            logger.error(f"Error processing chunk: {e}")
            cursor.execute('UPDATE processed_chunks SET status = ? WHERE chunk_name = ?',
                          ('error', chunk_name))
            conn.commit()
            conn.close()
            return False

    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
        return False
    finally:
        if conn:
            conn.close()

def store_data_in_db(conn, articles_df, entities_df, entity_stats_df):
    """
    Store processed data in the database

    Args:
        conn: Database connection
        articles_df: DataFrame containing articles
        entities_df: DataFrame containing entity mentions
        entity_stats_df: DataFrame containing entity statistics
    """
    cursor = conn.cursor()

    # Store articles
    fetch_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    for _, article in articles_df.iterrows():
        cursor.execute('''
        INSERT OR IGNORE INTO articles
        (url, title, title_translated, seendate, language, domain, sourcecountry, theme_id, theme_description,
         fetch_date, trust_score, sentiment_polarity, content_hash)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            article.get('url', ''),
            article.get('title', ''),
            article.get('title_translated', article.get('title', '')),
            article.get('seendate', ''),
            article.get('language', ''),
            article.get('domain', ''),
            article.get('sourcecountry', ''),
            article.get('theme_id', ''),
            article.get('theme_description', ''),
            fetch_date,
            float(article.get('trust_score', 0.5)),
            float(article.get('sentiment_polarity', 0.0)),
            article.get('content_hash', '')
        ))

    # Get article IDs
    article_ids = {}
    for _, article in articles_df.iterrows():
        cursor.execute('SELECT id FROM articles WHERE url = ?', (article.get('url', ''),))
        result = cursor.fetchone()
        if result:
            article_ids[article.get('url', '')] = result[0]

    # Store entities
    for _, entity_stat in entity_stats_df.iterrows():
        cursor.execute('''
        INSERT OR IGNORE INTO entities
        (text, type, count, num_sources, source_diversity, trust_score)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            entity_stat.get('entity', ''),
            entity_stat.get('type', ''),
            int(entity_stat.get('count', 0)),
            int(entity_stat.get('num_sources', 0)),
            float(entity_stat.get('source_diversity', 0.0)),
            float(entity_stat.get('trust_score', 0.5))
        ))

        # Get entity ID
        cursor.execute('SELECT id FROM entities WHERE text = ? AND type = ?',
                      (entity_stat.get('entity', ''), entity_stat.get('type', '')))
        entity_id = cursor.fetchone()[0]

        # Store article-entity relationships
        entity_mentions = entities_df[entities_df['text'] == entity_stat.get('entity', '')]
        for _, mention in entity_mentions.iterrows():
            article_id = article_ids.get(mention.get('article_url', ''))
            if article_id:
                cursor.execute('''
                INSERT OR IGNORE INTO article_entities
                (article_id, entity_id, context)
                VALUES (?, ?, ?)
                ''', (
                    article_id,
                    entity_id,
                    mention.get('context', '')
                ))

    # Update source statistics
    for domain, group in articles_df.groupby('domain'):
        if not domain or pd.isna(domain):
            continue

        cursor.execute('''
        INSERT OR REPLACE INTO sources
        (domain, country, article_count, trust_score)
        VALUES (?, ?, ?, ?)
        ''', (
            domain,
            group.iloc[0].get('sourcecountry', ''),
            len(group),
            group['trust_score'].mean() if 'trust_score' in group else 0.5
        ))

    # Update theme statistics
    for theme_id, group in articles_df.groupby('theme_id'):
        if not theme_id or pd.isna(theme_id):
            continue

        cursor.execute('''
        INSERT OR REPLACE INTO themes
        (theme_id, description, article_count)
        VALUES (?, ?, ?)
        ''', (
            theme_id,
            group.iloc[0].get('theme_description', ''),
            len(group)
        ))

    # Commit changes
    conn.commit()
    logger.info("Stored processed data in database")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Process a single chunk of GDELT data')
    parser.add_argument('--chunk-path', type=str, required=True,
                        help='Path to the chunk CSV file')
    parser.add_argument('--db-path', type=str, default='analysis_gdelt_chunks/gdelt_news.db',
                        help='Path to the SQLite database file (if using SQLite)')
    parser.add_argument('--output-dir', type=str, default='analysis_gdelt_chunks',
                        help='Directory to save output files')
    parser.add_argument('--use-postgres', type=str, choices=['true', 'false'], default='true',
                        help='Whether to use PostgreSQL (true) or SQLite (false)')
    parser.add_argument('--postgres-host', type=str, default='localhost',
                        help='PostgreSQL host')
    parser.add_argument('--postgres-port', type=str, default='5432',
                        help='PostgreSQL port')
    parser.add_argument('--postgres-db', type=str, default='gdelt_news',
                        help='PostgreSQL database name')
    parser.add_argument('--postgres-user', type=str, default='postgres',
                        help='PostgreSQL user')
    parser.add_argument('--postgres-password', type=str, default='postgres',
                        help='PostgreSQL password')
    parser.add_argument('--config-path', type=str, default='config/database.json',
                        help='Path to database configuration file')
    args = parser.parse_args()

    # Determine whether to use PostgreSQL
    use_postgres = args.use_postgres.lower() == 'true'

    # Create database configuration
    if use_postgres:
        db_config = {
            'host': args.postgres_host,
            'port': int(args.postgres_port),
            'dbname': args.postgres_db,
            'user': args.postgres_user,
            'password': args.postgres_password
        }
    else:
        db_config = args.db_path

    # Process chunk
    success = process_chunk(args.chunk_path, db_config, args.output_dir, use_postgres)
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
