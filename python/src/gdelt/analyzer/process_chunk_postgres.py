#!/usr/bin/env python3
"""
Process a single chunk of GDELT data using PostgreSQL
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

def process_chunk(chunk_path, db_config=None, output_dir=None):
    """
    Process a single chunk of GDELT data using PostgreSQL

    Args:
        chunk_path: Path to the chunk CSV file
        db_config: PostgreSQL database configuration dictionary
        output_dir: Directory to save output files

    Returns:
        True if successful, False otherwise
    """
    logger.info(f"Processing chunk: {chunk_path}")

    # Extract chunk name from path
    chunk_name = os.path.basename(chunk_path)

    # Connect to PostgreSQL database
    try:
        # Get PostgreSQL adapter
        if isinstance(db_config, dict):
            # Use provided configuration
            db = get_postgres_adapter(**db_config)
        else:
            # Use default configuration or configuration from file
            db_config = get_database_config(db_config if isinstance(db_config, str) else None)
            db = get_postgres_adapter(**db_config['postgres'])

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

        # Load chunk data
        try:
            articles_df = pd.read_csv(chunk_path)
            logger.info(f"Loaded {len(articles_df)} articles from {chunk_path}")
        except Exception as e:
            logger.error(f"Error loading chunk data: {e}")
            db.execute_query(
                'UPDATE chunks SET status = %s WHERE name = %s',
                ('error', chunk_name),
                fetch=False
            )
            return False

        # Process articles
        try:
            # Initialize processors
            entity_extractor = SimpleEntityExtractor()
            sentiment_analyzer = SentimentAnalyzer()
            translator = ArticleTranslator(cache_dir=os.path.join(output_dir, 'translation_cache') if output_dir else 'translation_cache')

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
            store_data_in_db(db, articles_df, entities_df, entity_stats_df)

            # Update chunk status
            db.execute_query(
                '''
                UPDATE chunks
                SET status = %s
                WHERE name = %s
                ''',
                ('completed', chunk_name),
                fetch=False
            )

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
            db.execute_query(
                'UPDATE chunks SET status = %s WHERE name = %s',
                ('error', chunk_name),
                fetch=False
            )
            return False

    except Exception as e:
        logger.error(f"Database error: {e}")
        return False

def store_data_in_db(db, articles_df, entities_df, entity_stats_df):
    """
    Store processed data in the PostgreSQL database

    Args:
        db: PostgreSQL adapter
        articles_df: DataFrame containing articles
        entities_df: DataFrame containing entity mentions
        entity_stats_df: DataFrame containing entity statistics
    """
    # Store articles
    fetch_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    articles_stored = 0
    for _, article in articles_df.iterrows():
        try:
            # Make sure we have a valid URL
            url = article.get('url', '')
            if not url:
                logger.warning("Skipping article with empty URL")
                continue

            # Make sure we have a valid title
            title = article.get('title', '')
            if not title:
                logger.warning(f"Skipping article with empty title: {url}")
                continue

            # Handle missing or invalid values
            try:
                sentiment_polarity = float(article.get('sentiment_polarity', 0.0))
            except (ValueError, TypeError):
                sentiment_polarity = 0.0

            try:
                trust_score = float(article.get('trust_score', 0.5))
            except (ValueError, TypeError):
                trust_score = 0.5

            # Insert article
            result = db.execute_query(
                '''
                INSERT INTO articles
                (url, title, title_translated, seendate, language, domain, sourcecountry, theme_id, theme_description,
                 fetch_date, trust_score, sentiment_polarity, content_hash)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (url) DO UPDATE
                SET title = EXCLUDED.title,
                    title_translated = EXCLUDED.title_translated,
                    seendate = EXCLUDED.seendate,
                    language = EXCLUDED.language,
                    domain = EXCLUDED.domain,
                    sourcecountry = EXCLUDED.sourcecountry,
                    theme_id = EXCLUDED.theme_id,
                    theme_description = EXCLUDED.theme_description,
                    fetch_date = EXCLUDED.fetch_date,
                    trust_score = EXCLUDED.trust_score,
                    sentiment_polarity = EXCLUDED.sentiment_polarity,
                    content_hash = EXCLUDED.content_hash
                RETURNING id
                ''',
                (
                    url,
                    title,
                    article.get('title_translated', title),
                    article.get('seendate', ''),
                    article.get('language', ''),
                    article.get('domain', ''),
                    article.get('sourcecountry', ''),
                    article.get('theme_id', ''),
                    article.get('theme_description', ''),
                    fetch_date,
                    trust_score,
                    sentiment_polarity,
                    article.get('content_hash', '')
                )
            )

            if result:
                articles_stored += 1

        except Exception as e:
            logger.warning(f"Error storing article: {e}")
            continue

    logger.info(f"Stored {articles_stored} articles in database")

    # Get article IDs
    article_ids = {}
    for _, article in articles_df.iterrows():
        try:
            url = article.get('url', '')
            if not url:
                continue

            result = db.execute_query(
                'SELECT id FROM articles WHERE url = %s',
                (url,)
            )
            if result:
                article_ids[url] = result[0]['id']
        except Exception as e:
            logger.warning(f"Error getting article ID: {e}")
            continue

    # Store entities
    entities_stored = 0
    for _, entity_stat in entity_stats_df.iterrows():
        try:
            # Make sure we have a valid entity text
            entity_text = entity_stat.get('entity', '')
            if not entity_text:
                logger.warning("Skipping entity with empty text")
                continue

            # Make sure we have a valid entity type
            entity_type = entity_stat.get('type', '')
            if not entity_type:
                logger.warning(f"Skipping entity with empty type: {entity_text}")
                continue

            # Handle missing or invalid values
            try:
                count = int(entity_stat.get('count', 0))
            except (ValueError, TypeError):
                count = 0

            try:
                num_sources = int(entity_stat.get('num_sources', 0))
            except (ValueError, TypeError):
                num_sources = 0

            try:
                source_diversity = float(entity_stat.get('source_diversity', 0.0))
            except (ValueError, TypeError):
                source_diversity = 0.0

            try:
                trust_score = float(entity_stat.get('trust_score', 0.5))
            except (ValueError, TypeError):
                trust_score = 0.5

            # Insert entity
            result = db.execute_query(
                '''
                INSERT INTO entities
                (text, type, count, num_sources, source_diversity, trust_score)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (text, type) DO UPDATE
                SET count = EXCLUDED.count,
                    num_sources = EXCLUDED.num_sources,
                    source_diversity = EXCLUDED.source_diversity,
                    trust_score = EXCLUDED.trust_score
                RETURNING id
                ''',
                (
                    entity_text,
                    entity_type,
                    count,
                    num_sources,
                    source_diversity,
                    trust_score
                )
            )

            # Get entity ID
            if result:
                entities_stored += 1
                entity_id = result[0]['id']

                # Store article-entity relationships
                entity_mentions = entities_df[entities_df['text'] == entity_text]
                for _, mention in entity_mentions.iterrows():
                    try:
                        article_url = mention.get('article_url', '')
                        article_id = article_ids.get(article_url)
                        if article_id:
                            db.execute_query(
                                '''
                                INSERT INTO article_entities
                                (article_id, entity_id, context)
                                VALUES (%s, %s, %s)
                                ON CONFLICT (article_id, entity_id) DO UPDATE
                                SET context = EXCLUDED.context
                                ''',
                                (
                                    article_id,
                                    entity_id,
                                    mention.get('context', '')
                                ),
                                fetch=False
                            )
                    except Exception as e:
                        logger.warning(f"Error storing article-entity relationship: {e}")
                        continue
        except Exception as e:
            logger.warning(f"Error storing entity: {e}")
            continue

    logger.info(f"Stored {entities_stored} entities in database")

    # Update source statistics
    sources_stored = 0
    for domain, group in articles_df.groupby('domain'):
        try:
            if not domain or pd.isna(domain):
                continue

            # Get country
            country = ''
            if len(group) > 0 and 'sourcecountry' in group.iloc[0]:
                country = group.iloc[0].get('sourcecountry', '')

            # Calculate trust score
            try:
                trust_score = group['trust_score'].mean() if 'trust_score' in group else 0.5
            except Exception:
                trust_score = 0.5

            # Insert source
            db.execute_query(
                '''
                INSERT INTO sources
                (domain, country, article_count, trust_score)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (domain) DO UPDATE
                SET country = EXCLUDED.country,
                    article_count = EXCLUDED.article_count,
                    trust_score = EXCLUDED.trust_score
                ''',
                (
                    domain,
                    country,
                    len(group),
                    trust_score
                ),
                fetch=False
            )

            sources_stored += 1
        except Exception as e:
            logger.warning(f"Error storing source: {e}")
            continue

    logger.info(f"Stored {sources_stored} sources in database")

    logger.info("Stored processed data in database")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Process a single chunk of GDELT data using PostgreSQL')
    parser.add_argument('--chunk-path', type=str, required=True,
                        help='Path to the chunk CSV file')
    parser.add_argument('--output-dir', type=str, default='analysis_gdelt_chunks',
                        help='Directory to save output files')
    parser.add_argument('--config-path', type=str, default='config/database.json',
                        help='Path to database configuration file')
    parser.add_argument('--postgres-host', type=str, default='localhost',
                        help='PostgreSQL host')
    parser.add_argument('--postgres-port', type=int, default=5432,
                        help='PostgreSQL port')
    parser.add_argument('--postgres-db', type=str, default='gdelt_news',
                        help='PostgreSQL database name')
    parser.add_argument('--postgres-user', type=str, default='postgres',
                        help='PostgreSQL user')
    parser.add_argument('--postgres-password', type=str, default='postgres',
                        help='PostgreSQL password')
    args = parser.parse_args()

    # Create database configuration
    db_config = {
        'host': args.postgres_host,
        'port': args.postgres_port,
        'dbname': args.postgres_db,
        'user': args.postgres_user,
        'password': args.postgres_password
    }

    # Process chunk
    success = process_chunk(args.chunk_path, db_config, args.output_dir)
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
