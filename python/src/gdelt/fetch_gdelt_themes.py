#!/usr/bin/env python3
"""
GDELT Theme Fetcher

This script fetches news articles from GDELT for multiple themes by running the single theme fetcher.
"""

import os
import json
import subprocess
import time
import random
import argparse
from tqdm import tqdm

def load_themes(file_path, max_themes=None):
    """Load themes from JSONL file"""
    themes = []
    with open(file_path, 'r') as f:
        for line in f:
            theme_data = json.loads(line)
            themes.append(theme_data)
    
    # Sort by count (descending)
    themes.sort(key=lambda x: x.get('count', 0), reverse=True)
    
    # Limit to max_themes if specified
    if max_themes is not None:
        themes = themes[:max_themes]
    
    return themes

def fetch_theme(theme_id, theme_description):
    """Fetch articles for a single theme using the single theme fetcher"""
    cmd = ["python", "fetch_single_theme.py", theme_id, theme_description]
    
    try:
        # Run the command
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error fetching theme {theme_id}: {e}")
        return False

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Fetch GDELT articles for multiple themes')
    parser.add_argument('--themes-file', default="gdelt_useful_themes.jsonl", help='Path to themes JSONL file')
    parser.add_argument('--max-themes', type=int, default=30, help='Maximum number of themes to fetch')
    parser.add_argument('--delay', type=float, default=2.0, help='Delay between theme fetches in seconds')
    args = parser.parse_args()
    
    # Load themes
    print(f"Loading themes from {args.themes_file}...")
    themes = load_themes(args.themes_file, args.max_themes)
    print(f"Loaded {len(themes)} themes")
    
    # Fetch articles for each theme
    successful_themes = 0
    
    for theme in tqdm(themes, desc="Fetching themes"):
        theme_id = theme['theme']
        theme_description = theme['description']
        
        print(f"\nFetching articles for theme {theme_id} ({theme_description})...")
        
        # Fetch articles for this theme
        success = fetch_theme(theme_id, theme_description)
        
        if success:
            successful_themes += 1
        
        # Add a delay to avoid rate limiting
        time.sleep(args.delay + random.random())
    
    print(f"\nFetched articles for {successful_themes} out of {len(themes)} themes")
    
    # Merge the theme files
    print("\nMerging theme files...")
    subprocess.run(["python", "merge_gdelt_themes.py"], check=True)

if __name__ == "__main__":
    main()
