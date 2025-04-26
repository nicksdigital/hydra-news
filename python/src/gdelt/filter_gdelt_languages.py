#!/usr/bin/env python3
"""
GDELT Dataset Language Filter

This script filters the GDELT dataset to include only articles in specified languages.
"""

import os
import json
import pandas as pd
import datetime

# Configuration
INPUT_DIR = "dataset_gdelt_month"
OUTPUT_DIR = "dataset_gdelt_en_fr"
LANGUAGES = ["English", "French"]  # Languages to keep

def main():
    print(f"Filtering GDELT dataset to include only {', '.join(LANGUAGES)} articles...")
    
    # Load the dataset
    input_file = os.path.join(INPUT_DIR, "all_articles.csv")
    print(f"Loading dataset from {input_file}...")
    
    try:
        all_articles = pd.read_csv(input_file)
        print(f"Loaded {len(all_articles)} articles")
        
        # Filter by language
        filtered_articles = all_articles[all_articles['language'].isin(LANGUAGES)]
        print(f"Filtered to {len(filtered_articles)} articles in {', '.join(LANGUAGES)}")
        
        # Create output directory if it doesn't exist
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        # Save filtered articles
        output_file = os.path.join(OUTPUT_DIR, "all_articles.csv")
        filtered_articles.to_csv(output_file, index=False)
        print(f"Saved filtered articles to {output_file}")
        
        # Copy themes.json
        input_themes = os.path.join(INPUT_DIR, "themes.json")
        output_themes = os.path.join(OUTPUT_DIR, "themes.json")
        with open(input_themes, 'r') as f:
            themes = json.load(f)
        with open(output_themes, 'w') as f:
            json.dump(themes, f, indent=2)
        print(f"Copied themes to {output_themes}")
        
        # Create a new summary file
        theme_counts = filtered_articles['theme_id'].value_counts().to_dict()
        language_counts = filtered_articles['language'].value_counts().to_dict()
        
        summary = {
            'total_articles': len(filtered_articles),
            'total_themes': len(filtered_articles['theme_id'].unique()),
            'total_languages': len(language_counts),
            'articles_per_theme': theme_counts,
            'articles_per_language': language_counts,
            'filter_date': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'timespan': '1 month',
            'languages': LANGUAGES
        }
        
        summary_path = os.path.join(OUTPUT_DIR, "summary.json")
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        print(f"Saved summary to {summary_path}")
        
        # Print language statistics
        print("\nLanguage statistics:")
        for lang, count in language_counts.items():
            print(f"  - {lang}: {count} articles")
        
        print(f"\nSuccessfully filtered dataset to {len(filtered_articles)} articles in {', '.join(LANGUAGES)}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
