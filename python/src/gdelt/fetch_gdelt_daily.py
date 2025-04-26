#!/usr/bin/env python3
"""
GDELT Daily News Fetcher

This script fetches at least 100 English and French news articles per day from GDELT
for the past week, continuing requests until the target is reached.
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
OUTPUT_DIR = "dataset_gdelt_daily"
TARGET_ARTICLES_PER_DAY = 100  # Target number of articles per day
DAYS_TO_FETCH = 7  # Number of days to fetch (past week)
RATE_LIMIT_DELAY = 1  # Seconds between API calls to avoid rate limiting
LANGUAGES = ["English", "French"]  # Languages to fetch
MAX_ATTEMPTS_PER_DAY = 20  # Maximum number of attempts per day
ARTICLES_PER_REQUEST = 250  # Maximum allowed by GDELT API

def get_date_range():
    """Get date range for the past week"""
    end_date = datetime.datetime.now() - datetime.timedelta(days=1)  # Yesterday
    start_date = end_date - datetime.timedelta(days=DAYS_TO_FETCH-1)  # 7 days before yesterday

    # Generate a list of dates
    dates = []
    current_date = start_date
    while current_date <= end_date:
        dates.append(current_date.strftime('%Y-%m-%d'))
        current_date += datetime.timedelta(days=1)

    return dates

def fetch_articles_for_date(date_str, language):
    """Fetch articles for a specific date and language"""
    try:
        # Initialize GDELT client
        client = GdeltDoc()

        # Create date range for the specific day (start and end are the same)
        start_date = date_str
        end_date = date_str

        # Create filters
        filters = Filters(
            start_date=start_date,
            end_date=end_date,
            language=language,
            num_records=ARTICLES_PER_REQUEST
        )

        # Fetch articles
        articles = client.article_search(filters)

        # Add date and language information
        if not articles.empty:
            articles['fetch_date'] = date_str
            articles['target_language'] = language

            print(f"  - Found {len(articles)} {language} articles for {date_str}")

        return articles
    except Exception as e:
        print(f"  - Error fetching {language} articles for {date_str}: {e}")
        return pd.DataFrame()

def fetch_articles_with_keyword(date_str, language, keyword):
    """Fetch articles for a specific date, language, and keyword"""
    try:
        # Initialize GDELT client
        client = GdeltDoc()

        # Create date range for the specific day (start and end are the same)
        start_date = date_str
        end_date = date_str

        # Create filters
        filters = Filters(
            start_date=start_date,
            end_date=end_date,
            language=language,
            keyword=keyword,
            num_records=ARTICLES_PER_REQUEST
        )

        # Fetch articles
        articles = client.article_search(filters)

        # Add date and language information
        if not articles.empty:
            articles['fetch_date'] = date_str
            articles['target_language'] = language
            articles['keyword'] = keyword

            print(f"  - Found {len(articles)} {language} articles for {date_str} with keyword '{keyword}'")

        return articles
    except Exception as e:
        print(f"  - Error fetching {language} articles for {date_str} with keyword '{keyword}': {e}")
        return pd.DataFrame()

def save_dataset(all_articles):
    """Save the dataset to CSV and JSON files"""
    # Create output directory if it doesn't exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Save all articles to CSV
    all_articles_path = os.path.join(OUTPUT_DIR, "all_articles.csv")
    all_articles.to_csv(all_articles_path, index=False)
    print(f"Saved all articles to {all_articles_path}")

    # Save articles by date
    dates_dir = os.path.join(OUTPUT_DIR, "dates")
    os.makedirs(dates_dir, exist_ok=True)

    for date_str in all_articles['fetch_date'].unique():
        date_articles = all_articles[all_articles['fetch_date'] == date_str]
        date_file = os.path.join(dates_dir, f"{date_str}.csv")
        date_articles.to_csv(date_file, index=False)

    print(f"Saved articles by date to {dates_dir}")

    # Save articles by language
    languages_dir = os.path.join(OUTPUT_DIR, "languages")
    os.makedirs(languages_dir, exist_ok=True)

    for language in all_articles['language'].unique():
        language_articles = all_articles[all_articles['language'] == language]
        language_file = os.path.join(languages_dir, f"{language}.csv")
        language_articles.to_csv(language_file, index=False)

    print(f"Saved articles by language to {languages_dir}")

    # Create a summary file
    date_counts = all_articles.groupby(['fetch_date', 'language']).size().unstack(fill_value=0).to_dict()
    language_counts = all_articles['language'].value_counts().to_dict()

    summary = {
        'total_articles': len(all_articles),
        'articles_per_date': {date: len(all_articles[all_articles['fetch_date'] == date]) for date in all_articles['fetch_date'].unique()},
        'articles_per_language': language_counts,
        'articles_per_date_language': date_counts,
        'fetch_date': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'target_languages': LANGUAGES,
        'target_articles_per_day': TARGET_ARTICLES_PER_DAY
    }

    summary_path = os.path.join(OUTPUT_DIR, "summary.json")
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"Saved summary to {summary_path}")

def main():
    # Get date range
    dates = get_date_range()
    print(f"Fetching articles for dates: {', '.join(dates)}")

    # Keywords to try if we don't get enough articles
    keywords = [
        "news", "politics", "economy", "health", "climate",
        "technology", "science", "sports", "entertainment", "business"
    ]

    # Fetch articles for each date and language
    all_articles = pd.DataFrame()

    for date_str in tqdm(dates, desc="Fetching dates"):
        date_articles = pd.DataFrame()

        for language in LANGUAGES:
            print(f"Fetching {language} articles for {date_str}")

            # First try without keyword
            articles = fetch_articles_for_date(date_str, language)

            if not articles.empty:
                date_articles = pd.concat([date_articles, articles], ignore_index=True)

            # Check if we have enough articles for this language and date
            # Initialize language_count to 0 if date_articles is empty
            language_count = 0
            if not date_articles.empty and 'language' in date_articles.columns:
                language_count = len(date_articles[date_articles['language'] == language])
            attempts = 0

            # If we don't have enough articles, try with keywords
            while language_count < TARGET_ARTICLES_PER_DAY and attempts < MAX_ATTEMPTS_PER_DAY:
                keyword = random.choice(keywords)
                print(f"  - Not enough articles ({language_count}/{TARGET_ARTICLES_PER_DAY}). Trying with keyword: {keyword}")

                # Fetch articles with keyword
                keyword_articles = fetch_articles_with_keyword(date_str, language, keyword)

                if not keyword_articles.empty:
                    date_articles = pd.concat([date_articles, keyword_articles], ignore_index=True)

                    # Remove duplicates
                    date_articles = date_articles.drop_duplicates(subset=['url'])

                    # Update count
                    language_count = len(date_articles[date_articles['language'] == language])
                    print(f"  - Now have {language_count}/{TARGET_ARTICLES_PER_DAY} {language} articles for {date_str}")

                attempts += 1

                # Add a delay to avoid rate limiting
                time.sleep(RATE_LIMIT_DELAY + random.random())

            print(f"  - Final count: {language_count}/{TARGET_ARTICLES_PER_DAY} {language} articles for {date_str}")

        # Add to all articles
        if not date_articles.empty:
            all_articles = pd.concat([all_articles, date_articles], ignore_index=True)

        # Print summary for this date
        print(f"Fetched {len(date_articles)} articles for {date_str}")
        for language in LANGUAGES:
            language_count = len(date_articles[date_articles['language'] == language])
            print(f"  - {language}: {language_count} articles")

    # Remove duplicates (same URL across different dates)
    original_count = len(all_articles)
    all_articles = all_articles.drop_duplicates(subset=['url'])
    print(f"Removed {original_count - len(all_articles)} duplicate articles")

    # Print language statistics
    print("\nLanguage statistics:")
    language_counts = all_articles['language'].value_counts()
    for lang, count in language_counts.items():
        print(f"  - {lang}: {count} articles")

    print(f"\nFetched {len(all_articles)} unique articles across {len(dates)} days")

    # Save the dataset
    save_dataset(all_articles)

if __name__ == "__main__":
    main()
