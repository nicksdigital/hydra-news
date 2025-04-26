#!/usr/bin/env python3
"""
GDELT Data Fetcher

This script fetches news articles from the GDELT API based on themes from the past week
and creates a structured dataset for analysis.
"""

import os
import json
import pandas as pd
import datetime
from tqdm import tqdm
import time
import random
from gdeltdoc import GdeltDoc, Filters

# Configuration
OUTPUT_DIR = "dataset_gdelt"
THEMES_FILE = "gdelt_useful_themes.jsonl"
MAX_ARTICLES_PER_THEME = 100  # Number of articles per theme
RATE_LIMIT_DELAY = 1  # Seconds between API calls to avoid rate limiting
MAX_THEMES = 30  # Process fewer themes for a more focused dataset
MAX_DATASET_SIZE_GB = 10  # Maximum dataset size in GB
ESTIMATED_ARTICLE_SIZE_KB = 10  # Estimated average size per article in KB
LANGUAGES = ["en", "fr"]  # English and French articles
TIMESPAN = "1week"  # Use a shorter timespan for more reliable results

def load_themes(file_path):
    """Load themes from JSONL file"""
    themes = []
    with open(file_path, 'r') as f:
        for line in f:
            theme_data = json.loads(line)
            themes.append(theme_data)

    # Sort by count (descending)
    themes.sort(key=lambda x: x.get('count', 0), reverse=True)

    # Limit to MAX_THEMES
    return themes[:MAX_THEMES]

def get_date_range():
    """Get date range for the past 3 months (GDELT API limitation)"""
    end_date = datetime.datetime.now()
    start_date = end_date - datetime.timedelta(days=90)  # 3 months (API limitation)
    return start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')

def fetch_articles_for_theme(theme_id, theme_description):
    """Fetch English and French articles for a specific theme using keyword search"""
    try:
        # Initialize GDELT client
        client = GdeltDoc()
        all_articles = pd.DataFrame()

        # Use the theme description as a keyword search
        # This is more reliable than using the theme parameter
        keyword = theme_id.replace("_", " ").lower()

        # For each language
        for language in LANGUAGES:
            try:
                print(f"Fetching {language} articles for keyword '{keyword}'")

                # Create filters for keyword search
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

def save_dataset(all_articles, themes_map, output_dir):
    """Save the dataset to CSV and JSON files"""
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Save all articles to CSV
    all_articles_path = os.path.join(output_dir, "all_articles.csv")
    all_articles.to_csv(all_articles_path, index=False)
    print(f"Saved all articles to {all_articles_path}")

    # Save theme information
    themes_path = os.path.join(output_dir, "themes.json")
    with open(themes_path, 'w') as f:
        json.dump(themes_map, f, indent=2)
    print(f"Saved theme information to {themes_path}")

    # Check if we have any articles
    if all_articles.empty:
        print("No articles found. Skipping theme-specific files.")

        # Create a summary file with zeros
        summary = {
            'total_articles': 0,
            'total_themes': 0,
            'articles_per_theme': {},
            'fetch_date': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'date_range': {
                'start_date': start_date,
                'end_date': end_date
            }
        }
    else:
        # Save articles by theme
        themes_dir = os.path.join(output_dir, "themes")
        os.makedirs(themes_dir, exist_ok=True)

        for theme_id in all_articles['theme_id'].unique():
            theme_articles = all_articles[all_articles['theme_id'] == theme_id]
            theme_file = os.path.join(themes_dir, f"{theme_id}.csv")
            theme_articles.to_csv(theme_file, index=False)

        print(f"Saved articles by theme to {themes_dir}")

        # Create a summary file
        summary = {
            'total_articles': len(all_articles),
            'total_themes': len(all_articles['theme_id'].unique()),
            'articles_per_theme': all_articles.groupby('theme_id').size().to_dict(),
            'fetch_date': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'date_range': {
                'start_date': start_date,
                'end_date': end_date
            }
        }

    summary_path = os.path.join(output_dir, "summary.json")
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"Saved summary to {summary_path}")

def main():
    # Load themes
    print(f"Loading themes from {THEMES_FILE}...")
    themes = load_themes(THEMES_FILE)
    print(f"Loaded {len(themes)} themes")

    # Create a map of theme_id to description
    themes_map = {theme['theme']: theme['description'] for theme in themes}

    # Get date range
    global start_date, end_date
    start_date, end_date = get_date_range()
    print(f"Fetching articles from {start_date} to {end_date}")

    # Calculate maximum number of articles based on size limit
    max_articles = (MAX_DATASET_SIZE_GB * 1024 * 1024) // ESTIMATED_ARTICLE_SIZE_KB
    print(f"Maximum dataset size: {MAX_DATASET_SIZE_GB} GB (~{max_articles} articles)")

    # Fetch articles for each theme
    all_articles = pd.DataFrame()
    processed_themes = 0

    for theme in tqdm(themes, desc="Fetching articles"):
        theme_id = theme['theme']
        theme_description = theme['description']

        # Fetch articles for this theme
        articles = fetch_articles_for_theme(theme_id, theme_description)

        # Add to all articles
        if not articles.empty:
            all_articles = pd.concat([all_articles, articles], ignore_index=True)

            # Check if we've exceeded the size limit
            if len(all_articles) > max_articles:
                print(f"Reached size limit of {MAX_DATASET_SIZE_GB} GB. Stopping fetch.")
                # Keep only up to max_articles
                all_articles = all_articles.head(max_articles)
                break

        processed_themes += 1

        # Add a delay to avoid rate limiting
        time.sleep(RATE_LIMIT_DELAY + random.random())

    # Remove duplicates (same URL across different themes)
    all_articles = all_articles.drop_duplicates(subset=['url'])

    print(f"Fetched {len(all_articles)} unique articles across {processed_themes} themes")
    print(f"Estimated dataset size: {len(all_articles) * ESTIMATED_ARTICLE_SIZE_KB / (1024 * 1024):.2f} GB")

    # Save the dataset
    save_dataset(all_articles, themes_map, OUTPUT_DIR)

if __name__ == "__main__":
    main()
