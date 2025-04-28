#!/usr/bin/env python3
"""
Test script for the enhanced GDELT fetcher
"""

import logging
import pandas as pd
import sys
import traceback
from datetime import datetime, timedelta

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,  # Set to DEBUG for more verbose output
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import the fetch_gdelt_data function
from enhanced_gdelt_fetcher import fetch_gdelt_data

def main():
    """Main function"""
    try:
        # Get date range for the last 3 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)

        # Format dates as strings
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')

        logger.info(f"Testing GDELT fetcher with date range: {start_date_str} to {end_date_str}")

        # Test with a specific keyword first (more likely to succeed)
        logger.info("Testing with keyword 'climate change'...")
        try:
            keyword_articles = fetch_gdelt_data(start_date_str, end_date_str, max_articles=20, keyword="climate change")

            if len(keyword_articles) > 0:
                logger.info(f"Successfully fetched {len(keyword_articles)} articles about 'climate change'")
                logger.info(f"Sample article: {keyword_articles.iloc[0]['title']}")

                # Show column names
                logger.info(f"Available columns: {keyword_articles.columns.tolist()}")
            else:
                logger.warning("No articles fetched for the keyword 'climate change'")
        except Exception as e:
            logger.error(f"Error testing with keyword: {e}")
            traceback.print_exc()

        # Test with default parameters
        logger.info("Testing with default parameters...")
        try:
            articles = fetch_gdelt_data(start_date_str, end_date_str, max_articles=50)

            if len(articles) > 0:
                logger.info(f"Successfully fetched {len(articles)} articles")
                logger.info(f"Sample article: {articles.iloc[0]['title']}")

                # Show first 5 articles
                for i, article in articles.head(5).iterrows():
                    logger.info(f"Article {i+1}: {article['title']} - {article['url']}")
            else:
                logger.warning("No articles fetched with default parameters")
        except Exception as e:
            logger.error(f"Error testing with default parameters: {e}")
            traceback.print_exc()

    except Exception as e:
        logger.error(f"Unexpected error in main function: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
