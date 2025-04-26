#!/usr/bin/env python3
"""
GDELT Comprehensive News Fetcher

This script fetches news articles from GDELT using the gdeltdoc Python module.
It supports fetching articles in multiple languages and provides robust
error handling and rate limiting.

Features:
- Fetches articles for multiple themes
- Supports multiple languages
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
import logging
from gdeltdoc import GdeltDoc, Filters

def setup_logging(log_file=None, level=logging.INFO):
    """Set up logging configuration"""
    handlers = [logging.StreamHandler()]
    
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=handlers
    )
    
    return logging.getLogger(__name__)

def load_themes(themes_file, max_themes=None):
    """
    Load themes from a JSONL file
    
    Args:
        themes_file: Path to themes JSONL file
        max_themes: Maximum number of themes to load
        
    Returns:
        List of theme dictionaries
    """
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

def fetch_articles_for_theme(theme_id, theme_description, languages, timespan, max_articles, max_retries=3, rate_limit_delay=1):
    """
    Fetch articles for a specific theme in multiple languages
    
    Args:
        theme_id: Theme ID
        theme_description: Theme description
        languages: List of languages to fetch
        timespan: Timespan for fetching articles (e.g., "1m" for 1 month)
        max_articles: Maximum number of articles per theme and language
        max_retries: Maximum number of retries for failed API calls
        rate_limit_delay: Delay between API calls to avoid rate limiting
        
    Returns:
        DataFrame with fetched articles
    """
    logger = logging.getLogger(__name__)
    all_articles = pd.DataFrame()
    
    # Use the theme ID as a keyword search
    # This is more reliable than using the theme parameter
    keyword = theme_id.replace("_", " ").lower()
    
    logger.info(f"Fetching articles for keyword '{keyword}'")
    
    for language in languages:
        logger.info(f"  - Language: {language}")
        
        for attempt in range(max_retries):
            try:
                # Initialize GDELT client
                client = GdeltDoc()
                
                # Create filters for keyword search
                filters = Filters(
                    keyword=keyword,
                    language=language,
                    timespan=timespan,
                    num_records=max_articles
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
                if attempt < max_retries - 1:
                    # Wait before retrying
                    retry_delay = (attempt + 1) * rate_limit_delay * 2
                    logger.info(f"    - Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    logger.error(f"    - Failed after {max_retries} attempts")
        
        # Add a delay to avoid rate limiting
        time.sleep(rate_limit_delay + random.random())
    
    # Remove duplicates (same URL)
    if not all_articles.empty:
        original_count = len(all_articles)
        all_articles = all_articles.drop_duplicates(subset=['url'])
        logger.info(f"  - After deduplication: {len(all_articles)} articles (removed {original_count - len(all_articles)} duplicates)")
    
    return all_articles

def save_dataset(all_articles, themes_map, output_dir):
    """
    Save the dataset to CSV and JSON files
    
    Args:
        all_articles: DataFrame with all articles
        themes_map: Dictionary mapping theme IDs to descriptions
        output_dir: Directory to save the dataset
    """
    logger = logging.getLogger(__name__)
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Save all articles to CSV
    all_articles_path = os.path.join(output_dir, "all_articles.csv")
    all_articles.to_csv(all_articles_path, index=False)
    logger.info(f"Saved all articles to {all_articles_path}")
    
    # Save theme information
    themes_path = os.path.join(output_dir, "themes.json")
    with open(themes_path, 'w') as f:
        json.dump(themes_map, f, indent=2)
    logger.info(f"Saved theme information to {themes_path}")
    
    # Save articles by theme
    themes_dir = os.path.join(output_dir, "themes")
    os.makedirs(themes_dir, exist_ok=True)
    
    for theme_id in all_articles['theme_id'].unique():
        theme_articles = all_articles[all_articles['theme_id'] == theme_id]
        theme_path = os.path.join(themes_dir, f"{theme_id}.csv")
        theme_articles.to_csv(theme_path, index=False)
    
    logger.info(f"Saved articles by theme to {themes_dir}")
    
    # Save articles by language
    languages_dir = os.path.join(output_dir, "languages")
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
    
    summary_path = os.path.join(output_dir, "summary.json")
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    logger.info(f"Saved summary to {summary_path}")

def fetch_gdelt_dataset(themes_file, output_dir, max_themes=30, max_articles=100, 
                       languages=None, timespan="1m", rate_limit_delay=1):
    """
    Fetch a GDELT dataset
    
    Args:
        themes_file: Path to themes JSONL file
        output_dir: Directory to save the dataset
        max_themes: Maximum number of themes to process
        max_articles: Maximum number of articles per theme and language
        languages: List of languages to fetch (default: ["English", "French"])
        timespan: Timespan for fetching articles (default: "1m" for 1 month)
        rate_limit_delay: Delay between API calls to avoid rate limiting
        
    Returns:
        Path to the dataset directory
    """
    logger = logging.getLogger(__name__)
    
    # Set default languages
    if languages is None:
        languages = ["English", "French"]
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Load themes
    logger.info(f"Loading themes from {themes_file}...")
    themes = load_themes(themes_file, max_themes)
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
        articles = fetch_articles_for_theme(
            theme_id, 
            theme_description, 
            languages, 
            timespan, 
            max_articles,
            rate_limit_delay=rate_limit_delay
        )
        
        # Add to all articles
        if not articles.empty:
            all_articles = pd.concat([all_articles, articles], ignore_index=True)
            successful_themes += 1
        
        # Add a delay to avoid rate limiting
        time.sleep(rate_limit_delay + random.random())
    
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
    save_dataset(all_articles, themes_map, output_dir)
    
    logger.info("Dataset creation complete!")
    return output_dir

def main():
    """Main entry point"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Fetch GDELT news articles")
    parser.add_argument("--themes-file", default="gdelt_useful_themes.jsonl", help="Path to themes JSONL file")
    parser.add_argument("--output-dir", default="dataset_gdelt_month", help="Output directory")
    parser.add_argument("--max-themes", type=int, default=30, help="Maximum number of themes to process")
    parser.add_argument("--max-articles", type=int, default=100, help="Maximum number of articles per theme and language")
    parser.add_argument("--languages", nargs="+", default=["English", "French"], help="Languages to fetch")
    parser.add_argument("--timespan", default="1m", help="Timespan for fetching articles (e.g., '1m' for 1 month)")
    parser.add_argument("--delay", type=float, default=1, help="Delay between API calls (seconds)")
    parser.add_argument("--log-file", default=None, help="Path to log file")
    args = parser.parse_args()
    
    # Set up logging
    log_file = args.log_file or os.path.join(args.output_dir, "fetch.log")
    logger = setup_logging(log_file)
    
    # Fetch the dataset
    fetch_gdelt_dataset(
        args.themes_file,
        args.output_dir,
        args.max_themes,
        args.max_articles,
        args.languages,
        args.timespan,
        args.delay
    )

if __name__ == "__main__":
    main()
