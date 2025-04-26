#!/usr/bin/env python3
"""
GDELT Theme Merger

This script merges all the theme-specific CSV files into a single dataset.
"""

import os
import json
import pandas as pd
import datetime
import glob

# Configuration
THEMES_DIR = "dataset_gdelt_themes"
OUTPUT_DIR = "dataset_gdelt"
LANGUAGES = ["en", "fr"]  # Filter for English and French articles

def load_themes_file(file_path):
    """Load themes from JSONL file"""
    themes = []
    with open(file_path, 'r') as f:
        for line in f:
            theme_data = json.loads(line)
            themes.append(theme_data)

    # Create a map of theme_id to description
    themes_map = {theme['theme']: theme['description'] for theme in themes}
    return themes_map

def merge_theme_files():
    """Merge all theme CSV files into a single dataset"""
    # Get all CSV files in the themes directory
    theme_files = glob.glob(os.path.join(THEMES_DIR, "*.csv"))

    if not theme_files:
        print("No theme files found in", THEMES_DIR)
        return None

    print(f"Found {len(theme_files)} theme files")

    # Read and concatenate all files
    all_articles = pd.DataFrame()
    theme_counts = {}

    for file_path in theme_files:
        theme_id = os.path.basename(file_path).replace(".csv", "")
        try:
            # Read the CSV file
            df = pd.read_csv(file_path)

            # Count articles for this theme
            theme_counts[theme_id] = len(df)

            # Add to all articles
            all_articles = pd.concat([all_articles, df], ignore_index=True)

            print(f"Added {len(df)} articles from theme {theme_id}")
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")

    # Filter for English and French articles
    if LANGUAGES:
        original_count = len(all_articles)
        all_articles = all_articles[all_articles['language'].isin(LANGUAGES)]
        print(f"Filtered to {len(all_articles)} articles in languages: {', '.join(LANGUAGES)} (removed {original_count - len(all_articles)} articles)")

    # Remove duplicates (same URL across different themes)
    original_count = len(all_articles)
    all_articles = all_articles.drop_duplicates(subset=['url'])
    print(f"Removed {original_count - len(all_articles)} duplicate articles")

    return all_articles, theme_counts

def save_dataset(all_articles, themes_map, theme_counts):
    """Save the merged dataset to CSV and JSON files"""
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

    # Create a summary file
    summary = {
        'total_articles': len(all_articles),
        'total_themes': len(theme_counts),
        'articles_per_theme': theme_counts,
        'languages': LANGUAGES if LANGUAGES else ["all"],
        'fetch_date': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'date_range': {
            'timespan': '1 week (1w)'
        }
    }

    summary_path = os.path.join(OUTPUT_DIR, "summary.json")
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"Saved summary to {summary_path}")

def main():
    # Load themes map
    themes_map = load_themes_file("gdelt_useful_themes.jsonl")

    # Merge theme files
    result = merge_theme_files()

    if result is None:
        print("No data to merge")
        return

    all_articles, theme_counts = result

    # Save the merged dataset
    save_dataset(all_articles, themes_map, theme_counts)

    print(f"Successfully merged {len(all_articles)} articles from {len(theme_counts)} themes")
    print(f"Estimated dataset size: {len(all_articles) * 10 / (1024 * 1024):.2f} GB")

if __name__ == "__main__":
    main()
