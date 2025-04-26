#!/usr/bin/env python3
"""
GDELT Single Theme Fetcher

This script fetches news articles from GDELT for a single theme and saves them to a CSV file.
"""

import os
import sys
import json
import pandas as pd
import datetime
import time
import random
import argparse
from gdeltdoc import GdeltDoc, Filters

# Configuration
OUTPUT_DIR = "dataset_gdelt_themes"
MAX_ARTICLES_PER_THEME = 100  # Number of articles per theme
RATE_LIMIT_DELAY = 1  # Seconds between API calls to avoid rate limiting
LANGUAGES = []  # Fetch articles in all languages and filter later
TIMESPAN = "1w"  # Use a shorter timespan (1 week) for more reliable results

def fetch_articles_for_theme(theme_id, theme_description):
    """Fetch articles for a specific theme using keyword search"""
    try:
        # Initialize GDELT client
        client = GdeltDoc()
        all_articles = pd.DataFrame()

        # Use the theme ID as a keyword search
        # This is more reliable than using the theme parameter
        keyword = theme_id.replace("_", " ").lower()

        # If languages are specified, fetch for each language
        if LANGUAGES:
            for language in LANGUAGES:
                try:
                    print(f"Fetching {language} articles for keyword '{keyword}'")

                    # Create filters for keyword search with language
                    filters = Filters(
                        keyword=keyword,
                        timespan=TIMESPAN,
                        language=language,
                        num_records=MAX_ARTICLES_PER_THEME
                    )

                    # Fetch articles
                    articles = client.article_search(filters)

                    # Add to all articles
                    if not articles.empty:
                        all_articles = pd.concat([all_articles, articles], ignore_index=True)
                        print(f"  - Found {len(articles)} {language} articles for '{keyword}'")

                    # Add a delay to avoid rate limiting
                    time.sleep(RATE_LIMIT_DELAY + random.random())
                except Exception as e:
                    print(f"  - Error fetching {language} articles for '{keyword}': {e}")
                    continue
        else:
            # Fetch articles without language filter
            try:
                print(f"Fetching articles for keyword '{keyword}' (all languages)")

                # Create filters for keyword search without language
                filters = Filters(
                    keyword=keyword,
                    timespan=TIMESPAN,
                    num_records=MAX_ARTICLES_PER_THEME
                )

                # Fetch articles
                articles = client.article_search(filters)

                # Add to all articles
                if not articles.empty:
                    all_articles = pd.concat([all_articles, articles], ignore_index=True)

                    # Count articles by language
                    language_counts = articles['language'].value_counts()
                    for lang, count in language_counts.items():
                        print(f"  - Found {count} {lang} articles for '{keyword}'")

                    print(f"  - Total: {len(articles)} articles for '{keyword}'")

                # Add a delay to avoid rate limiting
                time.sleep(RATE_LIMIT_DELAY + random.random())
            except Exception as e:
                print(f"  - Error fetching articles for '{keyword}': {e}")
                return pd.DataFrame()

        # Add theme information to the articles
        if not all_articles.empty:
            all_articles['theme_id'] = theme_id
            all_articles['theme_description'] = theme_description

            # Remove duplicates (same URL)
            all_articles = all_articles.drop_duplicates(subset=['url'])

            print(f"Fetched {len(all_articles)} unique articles for theme {theme_id}")

        return all_articles
    except Exception as e:
        print(f"Error fetching articles for theme {theme_id}: {e}")
        return pd.DataFrame()

def save_theme_articles(articles, theme_id):
    """Save articles for a specific theme to a CSV file"""
    # Create output directory if it doesn't exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Save articles to CSV
    theme_file = os.path.join(OUTPUT_DIR, f"{theme_id}.csv")
    articles.to_csv(theme_file, index=False)
    print(f"Saved {len(articles)} articles for theme {theme_id} to {theme_file}")

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Fetch GDELT articles for a single theme')
    parser.add_argument('theme_id', help='Theme ID to fetch articles for')
    parser.add_argument('theme_description', help='Description of the theme')
    args = parser.parse_args()

    # Fetch articles for the theme
    articles = fetch_articles_for_theme(args.theme_id, args.theme_description)

    # Save articles
    if not articles.empty:
        save_theme_articles(articles, args.theme_id)
        print(f"Successfully fetched and saved {len(articles)} articles for theme {args.theme_id}")
    else:
        print(f"No articles found for theme {args.theme_id}")

if __name__ == "__main__":
    main()
