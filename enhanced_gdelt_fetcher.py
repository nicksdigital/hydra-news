#!/usr/bin/env python3
"""
Enhanced GDELT Fetcher

This script fetches more data from GDELT and processes it directly into the PostgreSQL database.
It supports parallel processing and can fetch data for multiple date ranges.
"""

import os
import sys
import json
import logging
import argparse
import pandas as pd
import concurrent.futures
from datetime import datetime, timedelta
from tqdm import tqdm

# Add the current directory to the path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from python.src.gdelt.database.postgres_adapter import get_postgres_adapter
from python.src.gdelt.config.database_config import get_database_config
from python.src.gdelt.analyzer.simple_entity_extractor import SimpleEntityExtractor
from python.src.gdelt.analyzer.sentiment_analyzer import SentimentAnalyzer

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def fetch_gdelt_data(start_date, end_date, max_articles=1000, keyword=None):
    """
    Fetch GDELT data for a specific date range

    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        max_articles: Maximum number of articles to fetch
        keyword: Optional keyword to filter articles

    Returns:
        DataFrame containing articles
    """
    try:
        import gdeltdoc
        from gdeltdoc import Filters

        logger.info(f"Fetching GDELT data from {start_date} to {end_date}")

        # List of reliable search queries that work with the GDELT API
        fallback_queries = [
            '"climate change"',
            '"world news"',
            '"international politics"',
            '"economic development"',
            '"technology innovation"',
            '"health crisis"',
            '"global pandemic"',
            '"environmental issues"',
            '"financial markets"',
            '"social media"'
        ]

        # Format the keyword properly for the GDELT API
        if keyword:
            # If keyword is a single word, append a common related term to make it at least 2 words
            words = keyword.split()
            if len(words) == 1:
                logger.info(f"Single word keyword '{keyword}' detected, expanding to ensure at least 2 words")
                search_query = f'"{keyword} news"'
            else:
                # Make sure the keyword is properly formatted with quotes if needed
                if not keyword.startswith('"') and ' ' in keyword:
                    search_query = f'"{keyword}"'
                else:
                    search_query = keyword
        else:
            # Default search with a reliable multi-word phrase
            search_query = fallback_queries[0]

        # Initialize GDELT client
        gd = gdeltdoc.GdeltDoc()

        # Try to fetch articles with the initial query
        try:
            # Create filters object with proper parameters
            filters = Filters(
                keyword=search_query,
                start_date=start_date,
                end_date=end_date,
                num_records=min(max_articles, 250)  # API limit is 250 per request
            )

            # Fetch articles with proper filters
            articles = gd.article_search(filters)

            if articles is None or len(articles) == 0:
                logger.warning(f"No articles found with query: {search_query}")
                # If no articles found, try fallback queries
                if not keyword:  # Only try fallbacks if no specific keyword was requested
                    for fallback_query in fallback_queries[1:]:  # Skip the first one as we already tried it
                        logger.info(f"Trying fallback query: {fallback_query}")
                        try:
                            fallback_filters = Filters(
                                keyword=fallback_query,
                                start_date=start_date,
                                end_date=end_date,
                                num_records=min(max_articles, 250)
                            )
                            fallback_articles = gd.article_search(fallback_filters)
                            if fallback_articles is not None and len(fallback_articles) > 0:
                                logger.info(f"Found {len(fallback_articles)} articles with fallback query: {fallback_query}")
                                articles = fallback_articles
                                search_query = fallback_query  # Update search query for potential additional batches
                                break
                        except Exception as e:
                            logger.warning(f"Error with fallback query '{fallback_query}': {e}")
                            continue
        except Exception as e:
            error_msg = str(e)
            logger.warning(f"Error with initial query '{search_query}': {error_msg}")

            # Check if the error is about keywords being too short, too long, or too common
            if "too short, too long or too common" in error_msg:
                logger.info("Detected keyword issue, trying with more specific queries")

                # Try with more specific queries
                for fallback_query in fallback_queries:
                    logger.info(f"Trying fallback query: {fallback_query}")
                    try:
                        fallback_filters = Filters(
                            keyword=fallback_query,
                            start_date=start_date,
                            end_date=end_date,
                            num_records=min(max_articles, 250)
                        )
                        articles = gd.article_search(fallback_filters)
                        if articles is not None and len(articles) > 0:
                            logger.info(f"Found {len(articles)} articles with fallback query: {fallback_query}")
                            search_query = fallback_query  # Update search query for potential additional batches
                            break
                    except Exception as e2:
                        logger.warning(f"Error with fallback query '{fallback_query}': {e2}")
                        continue
            else:
                # Re-raise the exception if it's not a keyword issue
                raise

        # If we need more than 250 articles, make multiple requests
        if articles is not None and max_articles > 250 and len(articles) > 0:
            logger.info(f"Fetched first batch of {len(articles)} articles, fetching more...")

            # Calculate how many additional batches we need
            remaining_batches = min((max_articles - 250) // 250 + 1, 15)  # Limit to reasonable number of batches

            for i in range(remaining_batches):
                try:
                    # Update page number for pagination (if supported)
                    # Note: GDELT API might not support true pagination, so results may overlap
                    additional_filters = Filters(
                        keyword=search_query,
                        start_date=start_date,
                        end_date=end_date,
                        num_records=250
                    )

                    additional_articles = gd.article_search(additional_filters)

                    if len(additional_articles) > 0:
                        # Append new articles, will handle duplicates later by URL
                        articles = pd.concat([articles, additional_articles], ignore_index=True)
                        logger.info(f"Fetched additional {len(additional_articles)} articles, total: {len(articles)}")
                    else:
                        # No more articles available
                        break

                except Exception as e:
                    logger.warning(f"Error fetching additional batch {i+1}: {e}")
                    break

            # Remove duplicates by URL
            if len(articles) > 0:
                articles = articles.drop_duplicates(subset=['url'])
                logger.info(f"After removing duplicates: {len(articles)} unique articles")

        if articles is None or len(articles) == 0:
            logger.warning(f"No articles found for {start_date} to {end_date}")
            return pd.DataFrame()

        # Limit to max_articles if we got more
        if len(articles) > max_articles:
            articles = articles.head(max_articles)

        logger.info(f"Successfully fetched {len(articles)} articles")
        return articles

    except Exception as e:
        logger.error(f"Error fetching GDELT data: {e}")
        # Return empty DataFrame instead of mock data
        return pd.DataFrame()

def process_articles(articles_df, db, entity_extractor, sentiment_analyzer):
    """
    Process articles and store them in the database

    Args:
        articles_df: DataFrame containing articles
        db: Database adapter
        entity_extractor: Entity extractor
        sentiment_analyzer: Sentiment analyzer

    Returns:
        Number of articles processed
    """
    if len(articles_df) == 0:
        return 0

    # Add trust score and content hash
    articles_df['trust_score'] = 0.5  # Default trust score
    articles_df['content_hash'] = articles_df['url'].apply(lambda x: hash(x))

    # Extract entities
    entities_df = entity_extractor.extract_entities_from_dataframe(articles_df)
    entity_stats_df = entity_extractor.calculate_entity_stats()

    # Analyze sentiment
    articles_df = sentiment_analyzer.analyze_dataframe(articles_df)

    # Store articles in database
    fetch_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    for _, article in articles_df.iterrows():
        try:
            # Insert article
            result = db.execute_query(
                '''
                INSERT INTO articles
                (url, title, seendate, language, domain, sourcecountry, theme_id, theme_description,
                 fetch_date, trust_score, sentiment_polarity, content_hash)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (url) DO UPDATE
                SET title = EXCLUDED.title,
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
                    article.get('url', ''),
                    article.get('title', ''),
                    article.get('seendate', ''),
                    article.get('language', ''),
                    article.get('domain', ''),
                    article.get('sourcecountry', ''),
                    article.get('theme', ''),  # Using 'theme' as theme_id
                    article.get('theme', ''),  # Using 'theme' as theme_description
                    fetch_date,
                    float(article.get('trust_score', 0.5)),
                    float(article.get('sentiment_polarity', 0.0)),
                    article.get('content_hash', '')
                )
            )
        except Exception as e:
            logger.warning(f"Error inserting article: {e}")
            continue

    # Store entities in database
    for _, entity_stat in entity_stats_df.iterrows():
        try:
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
                    entity_stat.get('entity', ''),
                    entity_stat.get('type', ''),
                    int(entity_stat.get('count', 0)),
                    int(entity_stat.get('num_sources', 0)),
                    float(entity_stat.get('source_diversity', 0.0)),
                    float(entity_stat.get('trust_score', 0.5))
                )
            )
        except Exception as e:
            logger.warning(f"Error inserting entity: {e}")
            continue

    # Get article IDs
    article_urls = articles_df['url'].tolist()
    article_ids = {}
    for url in article_urls:
        try:
            result = db.execute_query(
                'SELECT id FROM articles WHERE url = %s',
                (url,)
            )
            if result:
                article_ids[url] = result[0]['id']
        except Exception as e:
            logger.warning(f"Error getting article ID: {e}")
            continue

    # Get entity IDs
    entity_texts = entity_stats_df['entity'].tolist()
    entity_ids = {}
    for text in entity_texts:
        try:
            result = db.execute_query(
                'SELECT id, type FROM entities WHERE text = %s',
                (text,)
            )
            if result:
                for row in result:
                    entity_ids[(text, row['type'])] = row['id']
        except Exception as e:
            logger.warning(f"Error getting entity ID: {e}")
            continue

    # Store article-entity relationships
    for _, mention in entities_df.iterrows():
        try:
            article_id = article_ids.get(mention.get('article_url', ''))
            entity_id = entity_ids.get((mention.get('text', ''), mention.get('type', '')))

            if article_id and entity_id:
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
            logger.warning(f"Error inserting article-entity relationship: {e}")
            continue

    # Update source statistics
    for domain, group in articles_df.groupby('domain'):
        if not domain or pd.isna(domain):
            continue

        try:
            # Try with country column
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
                    group.iloc[0].get('sourcecountry', ''),
                    len(group),
                    group['trust_score'].mean() if 'trust_score' in group else 0.5
                ),
                fetch=False
            )
        except Exception as e:
            logger.warning(f"Error updating source statistics: {e}")
            continue

    return len(articles_df)

def process_date_range(start_date, end_date, max_articles, keyword, db_config):
    """
    Process a specific date range

    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        max_articles: Maximum number of articles to fetch
        keyword: Optional keyword to filter articles
        db_config: Database configuration

    Returns:
        Number of articles processed
    """
    # Get database adapter
    db = get_postgres_adapter(**db_config['postgres'])

    # Initialize processors
    entity_extractor = SimpleEntityExtractor()
    sentiment_analyzer = SentimentAnalyzer()

    # Fetch data
    articles_df = fetch_gdelt_data(start_date, end_date, max_articles, keyword)

    # Process articles
    num_processed = process_articles(articles_df, db, entity_extractor, sentiment_analyzer)

    return num_processed

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Enhanced GDELT Fetcher')
    parser.add_argument('--config-path', type=str, default='config/database.json',
                        help='Path to database configuration file')
    parser.add_argument('--days-back', type=int, default=30,
                        help='Number of days to fetch data for')
    parser.add_argument('--articles-per-day', type=int, default=100,
                        help='Maximum number of articles to fetch per day')
    parser.add_argument('--keyword', type=str,
                        help='Optional keyword to filter articles')
    parser.add_argument('--workers', type=int, default=4,
                        help='Number of worker processes')
    args = parser.parse_args()

    # Get database configuration
    db_config = get_database_config(args.config_path)

    # Generate date ranges
    date_ranges = []
    end_date = datetime.now()
    for _ in range(args.days_back):  # Use _ for unused loop variable
        start_date = end_date - timedelta(days=1)
        date_ranges.append((
            start_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d'),
            args.articles_per_day,
            args.keyword
        ))
        end_date = start_date

    # Process date ranges in parallel
    total_processed = 0
    with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers) as executor:
        futures = [
            executor.submit(process_date_range, start_date, end_date, max_articles, keyword, db_config)
            for start_date, end_date, max_articles, keyword in date_ranges
        ]

        for future in tqdm(concurrent.futures.as_completed(futures), total=len(futures), desc="Processing date ranges"):
            try:
                num_processed = future.result()
                total_processed += num_processed
            except Exception as e:
                logger.error(f"Error processing date range: {e}")

    logger.info(f"Total articles processed: {total_processed}")

if __name__ == '__main__':
    main()
