#!/usr/bin/env python3
"""
GDELT Comprehensive News Fetcher

This script fetches news articles from GDELT for the past month using the gdeltdoc Python module.
It supports fetching articles in multiple languages (English and French) and provides robust
error handling and rate limiting.

Features:
- Fetches articles for multiple themes from the past month
- Supports English and French languages
- Implements rate limiting to avoid API throttling
- Provides detailed progress reporting
- Creates a structured dataset for analysis
"""

import os
import json
import pandas as pd
import datetime
import time
import random
import argparse
from tqdm import tqdm
from gdeltdoc import GdeltDoc, Filters

# Configuration
OUTPUT_DIR = "dataset_gdelt_month"
THEMES_FILE = "gdelt_useful_themes.jsonl"
MAX_ARTICLES_PER_THEME = 100  # Number of articles per theme
RATE_LIMIT_DELAY = 1  # Seconds between API calls to avoid rate limiting
MAX_THEMES = 30  # Process fewer themes for a more focused dataset
LANGUAGES = ["English", "French"]  # Languages to fetch
TIMESPAN = "1m"  # 1 month timespan
MAX_RETRIES = 3  # Maximum number of retries for failed API calls

def setup_logging():
    """Set up logging configuration"""
    import logging
    
    # Create output directory if it doesn't exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Set up logging
    log_file = os.path.join(OUTPUT_DIR, "fetch_log.txt")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger(__name__)

def load_themes(themes_file, max_themes=None):
    """Load themes from a JSONL file"""
    themes = []
    
    with open(themes_file, 'r') as f:
        for line in f:
            theme = json.loads(line)
            themes.append(theme)
    
    # Sort themes by count (descending)
    themes.sort(key=lambda x: x.get('count', 0), reverse=True)
    
    # Limit the number of themes if specified
    if max_themes:
        themes = themes[:max_themes]
    
    return themes

def fetch_articles_for_theme(theme_id, theme_description, languages, logger):
    """Fetch articles for a specific theme in multiple languages"""
    all_articles = pd.DataFrame()
    
    # Use the theme ID as a keyword search
    # This is more reliable than using the theme parameter
    keyword = theme_id.replace("_", " ").lower()
    
    logger.info(f"Fetching articles for keyword '{keyword}'")
    
    for language in languages:
        logger.info(f"  - Language: {language}")
        
        for attempt in range(MAX_RETRIES):
            try:
                # Initialize GDELT client
                client = GdeltDoc()
                
                # Create filters for keyword search
                filters = Filters(
                    keyword=keyword,
                    language=language,
                    timespan=TIMESPAN,
                    num_records=MAX_ARTICLES_PER_THEME
                )
                
                # Fetch articles
                articles = client.article_search(filters)
                
                # Add theme and language information
                if not articles.empty:
                    articles['theme_id'] = theme_id
                    articles['theme_description'] = theme_description
                    articles['target_language'] = language
                    
                    # Count articles
                    logger.info(f"    - Found {len(articles)} {language} articles")
                    
                    # Add to all articles
                    all_articles = pd.concat([all_articles, articles], ignore_index=True)
                
                # Success, break the retry loop
                break
                
            except Exception as e:
                logger.error(f"Error fetching articles for theme {theme_id}, language {language}, attempt {attempt+1}: {e}")
                if attempt < MAX_RETRIES - 1:
                    # Wait before retrying
                    retry_delay = (attempt + 1) * RATE_LIMIT_DELAY * 2
                    logger.info(f"    - Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    logger.error(f"    - Failed after {MAX_RETRIES} attempts")
    
    # Remove duplicates (same URL)
    if not all_articles.empty:
        original_count = len(all_articles)
        all_articles = all_articles.drop_duplicates(subset=['url'])
        logger.info(f"  - After deduplication: {len(all_articles)} articles (removed {original_count - len(all_articles)} duplicates)")
    
    return all_articles

def save_dataset(all_articles, themes_map, logger):
    """Save the dataset to CSV and JSON files"""
    # Create output directory if it doesn't exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Save all articles to CSV
    all_articles_path = os.path.join(OUTPUT_DIR, "all_articles.csv")
    all_articles.to_csv(all_articles_path, index=False)
    logger.info(f"Saved all articles to {all_articles_path}")
    
    # Save theme information
    themes_path = os.path.join(OUTPUT_DIR, "themes.json")
    with open(themes_path, 'w') as f:
        json.dump(themes_map, f, indent=2)
    logger.info(f"Saved theme information to {themes_path}")
    
    # Save articles by theme
    themes_dir = os.path.join(OUTPUT_DIR, "themes")
    os.makedirs(themes_dir, exist_ok=True)
    
    for theme_id in all_articles['theme_id'].unique():
        theme_articles = all_articles[all_articles['theme_id'] == theme_id]
        theme_path = os.path.join(themes_dir, f"{theme_id}.csv")
        theme_articles.to_csv(theme_path, index=False)
    
    logger.info(f"Saved articles by theme to {themes_dir}")
    
    # Save articles by language
    languages_dir = os.path.join(OUTPUT_DIR, "languages")
    os.makedirs(languages_dir, exist_ok=True)
    
    for language in all_articles['language'].unique():
        language_articles = all_articles[all_articles['language'] == language]
        language_path = os.path.join(languages_dir, f"{language}.csv")
        language_articles.to_csv(language_path, index=False)
    
    logger.info(f"Saved articles by language to {languages_dir}")
    
    # Create a summary file
    date_range = {
        'start_date': all_articles['seendate'].min() if not all_articles.empty else None,
        'end_date': all_articles['seendate'].max() if not all_articles.empty else None
    }
    
    language_counts = all_articles['language'].value_counts().to_dict()
    theme_counts = all_articles['theme_id'].value_counts().to_dict()
    
    summary = {
        'total_articles': len(all_articles),
        'total_themes': len(all_articles['theme_id'].unique()),
        'total_languages': len(language_counts),
        'articles_per_theme': theme_counts,
        'articles_per_language': language_counts,
        'date_range': date_range,
        'fetch_date': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'timespan': '1 month'
    }
    
    summary_path = os.path.join(OUTPUT_DIR, "summary.json")
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    logger.info(f"Saved summary to {summary_path}")

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Fetch GDELT news articles for the past month")
    parser.add_argument("--themes-file", default=THEMES_FILE, help="Path to themes JSONL file")
    parser.add_argument("--output-dir", default=OUTPUT_DIR, help="Output directory")
    parser.add_argument("--max-themes", type=int, default=MAX_THEMES, help="Maximum number of themes to process")
    parser.add_argument("--max-articles", type=int, default=MAX_ARTICLES_PER_THEME, help="Maximum number of articles per theme")
    parser.add_argument("--delay", type=float, default=RATE_LIMIT_DELAY, help="Delay between API calls (seconds)")
    parser.add_argument("--languages", nargs="+", default=LANGUAGES, help="Languages to fetch")
    args = parser.parse_args()
    
    # Set up logging
    logger = setup_logging()
    
    # Update global variables from arguments
    global OUTPUT_DIR, MAX_ARTICLES_PER_THEME, RATE_LIMIT_DELAY
    OUTPUT_DIR = args.output_dir
    MAX_ARTICLES_PER_THEME = args.max_articles
    RATE_LIMIT_DELAY = args.delay
    
    # Load themes
    logger.info(f"Loading themes from {args.themes_file}...")
    themes = load_themes(args.themes_file, args.max_themes)
    logger.info(f"Loaded {len(themes)} themes")
    
    # Create a map of theme_id to description
    themes_map = {theme['theme']: theme['description'] for theme in themes}
    
    # Fetch articles for each theme
    all_articles = pd.DataFrame()
    successful_themes = 0
    
    for theme in tqdm(themes, desc="Fetching articles"):
        theme_id = theme['theme']
        theme_description = theme['description']
        
        # Fetch articles for this theme
        articles = fetch_articles_for_theme(theme_id, theme_description, args.languages, logger)
        
        # Add to all articles
        if not articles.empty:
            all_articles = pd.concat([all_articles, articles], ignore_index=True)
            successful_themes += 1
        
        # Add a delay to avoid rate limiting
        time.sleep(RATE_LIMIT_DELAY + random.random())
    
    # Remove duplicates (same URL across different themes)
    original_count = len(all_articles)
    all_articles = all_articles.drop_duplicates(subset=['url'])
    logger.info(f"Removed {original_count - len(all_articles)} duplicate articles across themes")
    
    # Print language statistics
    logger.info("\nLanguage statistics:")
    language_counts = all_articles['language'].value_counts()
    for lang, count in language_counts.items():
        logger.info(f"  - {lang}: {count} articles")
    
    logger.info(f"\nFetched {len(all_articles)} unique articles across {successful_themes} themes")
    
    # Save the dataset
    save_dataset(all_articles, themes_map, logger)
    
    logger.info("Dataset creation complete!")

if __name__ == "__main__":
    main()
