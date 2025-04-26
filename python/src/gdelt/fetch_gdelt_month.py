#!/usr/bin/env python3
"""
GDELT News Fetcher - 1 Month Dataset

This script fetches news articles from GDELT for the past month using simple keyword searches
based on themes from the GDELT Global Knowledge Graph.
"""

import os
import json
import pandas as pd
import datetime
import time
import random
from tqdm import tqdm
from gdeltdoc import GdeltDoc, Filters

# Configuration
OUTPUT_DIR = "dataset_gdelt_month"
THEMES_FILE = "gdelt_useful_themes.jsonl"
MAX_ARTICLES_PER_THEME = 100  # Number of articles per theme
RATE_LIMIT_DELAY = 1  # Seconds between API calls to avoid rate limiting
MAX_THEMES = 30  # Process fewer themes for a more focused dataset
TIMESPAN = "1m"  # 1 month timespan

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

def fetch_articles_for_theme(theme_id, theme_description):
    """Fetch articles for a specific theme using keyword search"""
    try:
        # Initialize GDELT client
        client = GdeltDoc()
        
        # Use the theme ID as a keyword search
        # This is more reliable than using the theme parameter
        keyword = theme_id.replace("_", " ").lower()
        
        print(f"Fetching articles for keyword '{keyword}'")
        
        # Create filters for keyword search
        filters = Filters(
            keyword=keyword,
            timespan=TIMESPAN,
            num_records=MAX_ARTICLES_PER_THEME
        )
        
        # Fetch articles
        articles = client.article_search(filters)
        
        # Add theme information to the articles
        if not articles.empty:
            articles['theme_id'] = theme_id
            articles['theme_description'] = theme_description
            
            # Count articles by language
            language_counts = articles['language'].value_counts()
            for lang, count in language_counts.items():
                print(f"  - Found {count} {lang} articles")
            
            print(f"  - Total: {len(articles)} articles")
            
            # Remove duplicates (same URL)
            articles = articles.drop_duplicates(subset=['url'])
            print(f"  - After deduplication: {len(articles)} articles")
        
        return articles
    except Exception as e:
        print(f"Error fetching articles for theme {theme_id}: {e}")
        return pd.DataFrame()

def save_dataset(all_articles, themes_map):
    """Save the dataset to CSV and JSON files"""
    # Create output directory if it doesn't exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Save all articles to CSV
    all_articles_path = os.path.join(OUTPUT_DIR, "all_articles.csv")
    all_articles.to_csv(all_articles_path, index=False)
    print(f"Saved all articles to {all_articles_path}")
    
    # Save theme information
    themes_path = os.path.join(OUTPUT_DIR, "themes.json")
    with open(themes_path, 'w') as f:
        json.dump(themes_map, f, indent=2)
    print(f"Saved theme information to {themes_path}")
    
    # Save articles by language
    languages_dir = os.path.join(OUTPUT_DIR, "languages")
    os.makedirs(languages_dir, exist_ok=True)
    
    for language in all_articles['language'].unique():
        language_articles = all_articles[all_articles['language'] == language]
        language_file = os.path.join(languages_dir, f"{language}.csv")
        language_articles.to_csv(language_file, index=False)
    
    print(f"Saved articles by language to {languages_dir}")
    
    # Create a summary file
    language_counts = all_articles['language'].value_counts().to_dict()
    theme_counts = all_articles['theme_id'].value_counts().to_dict()
    
    summary = {
        'total_articles': len(all_articles),
        'total_themes': len(all_articles['theme_id'].unique()),
        'total_languages': len(language_counts),
        'articles_per_theme': theme_counts,
        'articles_per_language': language_counts,
        'fetch_date': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'timespan': '1 month'
    }
    
    summary_path = os.path.join(OUTPUT_DIR, "summary.json")
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
    
    # Fetch articles for each theme
    all_articles = pd.DataFrame()
    
    for theme in tqdm(themes, desc="Fetching articles"):
        theme_id = theme['theme']
        theme_description = theme['description']
        
        # Fetch articles for this theme
        articles = fetch_articles_for_theme(theme_id, theme_description)
        
        # Add to all articles
        if not articles.empty:
            all_articles = pd.concat([all_articles, articles], ignore_index=True)
        
        # Add a delay to avoid rate limiting
        time.sleep(RATE_LIMIT_DELAY + random.random())
    
    # Remove duplicates (same URL across different themes)
    original_count = len(all_articles)
    all_articles = all_articles.drop_duplicates(subset=['url'])
    print(f"Removed {original_count - len(all_articles)} duplicate articles")
    
    # Print language statistics
    print("\nLanguage statistics:")
    language_counts = all_articles['language'].value_counts()
    for lang, count in language_counts.items():
        print(f"  - {lang}: {count} articles")
    
    print(f"\nFetched {len(all_articles)} unique articles across {len(themes)} themes")
    
    # Save the dataset
    save_dataset(all_articles, themes_map)

if __name__ == "__main__":
    main()
