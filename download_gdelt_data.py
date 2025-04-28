#!/usr/bin/env python3
"""
Download GDELT data using the GDELT API and store it in the PostgreSQL database
"""

import os
import sys
import logging
import argparse
import requests
import pandas as pd
import json
import time
from datetime import datetime, timedelta
from python.src.gdelt.database.postgres_adapter import get_postgres_adapter
from python.src.gdelt.config.database_config import get_database_config

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def download_gdelt_data(start_date, end_date, max_articles=1000, keyword=None):
    """
    Download GDELT data using the GDELT API

    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        max_articles: Maximum number of articles to download
        keyword: Optional keyword to filter articles

    Returns:
        DataFrame containing articles
    """
    try:
        # Use the GDELT API directly
        base_url = "https://api.gdeltproject.org/api/v2/doc/doc"

        # Build query
        query = f"sourcelang:eng"
        if keyword:
            query += f" {keyword}"

        # Format dates
        start_str = start_date.replace("-", "")
        end_str = end_date.replace("-", "")

        # Build URL
        url = f"{base_url}?query={query}&mode=artlist&format=json&startdatetime={start_str}000000&enddatetime={end_str}235959&maxrecords=100"

        logger.info(f"Downloading GDELT data from {start_date} to {end_date}")
        logger.info(f"URL: {url}")

        # Download data
        response = requests.get(url)

        if response.status_code != 200:
            logger.error(f"Error downloading GDELT data: {response.status_code} {response.text}")
            return pd.DataFrame()

        # Parse JSON
        data = response.json()

        if 'articles' not in data:
            logger.warning("No articles found in response")
            return pd.DataFrame()

        articles = data['articles']

        if not articles:
            logger.warning("No articles found")
            return pd.DataFrame()

        logger.info(f"Downloaded {len(articles)} articles")

        # Convert to DataFrame
        df = pd.DataFrame(articles)

        # Add additional columns
        df['seendate'] = pd.to_datetime(df['seendate']).dt.strftime('%Y-%m-%d %H:%M:%S')
        df['fetch_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        df['trust_score'] = 0.5  # Default trust score
        df['content_hash'] = df.apply(
            lambda row: hash(str(row.get('title', '')) + str(row.get('url', ''))),
            axis=1
        )

        return df

    except Exception as e:
        logger.error(f"Error downloading GDELT data: {e}")
        return pd.DataFrame()

def store_data_in_db(db, articles_df):
    """
    Store articles in the PostgreSQL database

    Args:
        db: PostgreSQL adapter
        articles_df: DataFrame containing articles

    Returns:
        Number of articles stored
    """
    if len(articles_df) == 0:
        return 0

    # Store articles
    fetch_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    stored_count = 0

    for _, article in articles_df.iterrows():
        try:
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
                    float(article.get('sentiment', 0.0)),
                    article.get('content_hash', '')
                )
            )

            if result:
                stored_count += 1
        except Exception as e:
            logger.warning(f"Error storing article: {e}")

    # Update source statistics
    for domain, group in articles_df.groupby('domain'):
        if not domain or pd.isna(domain):
            continue

        try:
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

    logger.info(f"Stored {stored_count} articles in database")
    return stored_count

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Download GDELT data and store it in the PostgreSQL database')
    parser.add_argument('--config-path', type=str, default='config/database.json',
                        help='Path to database configuration file')
    parser.add_argument('--days-back', type=int, default=30,
                        help='Number of days to download data for')
    parser.add_argument('--articles-per-day', type=int, default=100,
                        help='Maximum number of articles to download per day')
    parser.add_argument('--keyword', type=str, default='climate OR economy OR politics OR technology OR health',
                        help='Keyword to filter articles')
    args = parser.parse_args()

    # Get database configuration
    db_config = get_database_config(args.config_path)

    # Connect to PostgreSQL database
    db = get_postgres_adapter(**db_config['postgres'])

    # Download data for each day
    total_articles = 0
    end_date = datetime.now()

    for i in range(args.days_back):
        start_date = end_date - timedelta(days=1)

        # Download data
        articles_df = download_gdelt_data(
            start_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d'),
            args.articles_per_day,
            args.keyword
        )

        # Store data in database
        if len(articles_df) > 0:
            stored_count = store_data_in_db(db, articles_df)
            total_articles += stored_count

        end_date = start_date

        # Respect GDELT API rate limits (1 request every 5 seconds)
        logger.info("Waiting 6 seconds to respect GDELT API rate limits...")
        time.sleep(6)

    logger.info(f"Total articles downloaded and stored: {total_articles}")

if __name__ == '__main__':
    main()
