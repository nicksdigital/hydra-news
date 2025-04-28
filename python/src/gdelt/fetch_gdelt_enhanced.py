#!/usr/bin/env python3
"""
Enhanced GDELT Dataset Fetcher

This script fetches a large dataset of news articles from GDELT with improved
deduplication, incremental fetching, and better error handling.
"""

import os
import json
import pandas as pd
import datetime
import time
import random
import argparse
import logging
import hashlib
import sqlite3
from tqdm import tqdm
from gdeltdoc import GdeltDoc, Filters
from urllib.parse import urlparse

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Enhanced GDELT dataset fetcher')
    parser.add_argument('--output-dir', type=str, default='dataset_gdelt_enhanced',
                        help='Directory to save the dataset')
    parser.add_argument('--max-articles', type=int, default=4000,
                        help='Maximum number of articles to fetch')
    parser.add_argument('--timespan', type=str, default='1m',
                        help='Timespan for fetching articles (e.g., "1m" for 1 month)')
    parser.add_argument('--languages', type=str, nargs='+',
                        default=['English', 'French', 'Spanish', 'German', 'Chinese', 'Arabic', 'Russian', 'Japanese', 'Korean', 'Italian', 'Portuguese'],
                        help='Languages to fetch (e.g., "English" "French")')
    parser.add_argument('--delay', type=float, default=1.0,
                        help='Delay between API calls to avoid rate limiting')
    parser.add_argument('--themes-file', type=str, default='gdelt_useful_themes.jsonl',
                        help='Path to themes JSONL file')
    parser.add_argument('--incremental', action='store_true',
                        help='Enable incremental fetching (only fetch new articles)')
    parser.add_argument('--db-path', type=str, default=None,
                        help='Path to SQLite database for deduplication')
    parser.add_argument('--keywords', type=str, nargs='+',
                        default=[
                            # Countries and regions
                            'Russia', 'Ukraine', 'China', 'United States', 'European Union',
                            'India', 'Brazil', 'Japan', 'Germany', 'United Kingdom', 'France',
                            'Canada', 'Australia', 'South Korea', 'Israel', 'Iran', 'Saudi Arabia',
                            'Turkey', 'Egypt', 'South Africa', 'Nigeria', 'Mexico', 'Indonesia',
                            'Pakistan', 'Bangladesh', 'Vietnam', 'Philippines', 'Thailand',
                            'Middle East', 'Africa', 'Asia', 'Latin America', 'Caribbean',
                            'Eastern Europe', 'Western Europe', 'North America', 'South America',
                            'Central Asia', 'Southeast Asia', 'East Asia', 'North Africa',
                            'Sub-Saharan Africa', 'Oceania', 'Arctic', 'Antarctica',

                            # Global topics
                            'climate change', 'global warming', 'economy', 'inflation', 'recession',
                            'technology', 'artificial intelligence', 'cybersecurity', 'blockchain',
                            'health', 'pandemic', 'COVID-19', 'vaccine', 'medicine',
                            'politics', 'election', 'democracy', 'human rights', 'corruption',
                            'war', 'conflict', 'peace', 'diplomacy', 'nuclear weapons',
                            'trade', 'sanctions', 'tariffs', 'supply chain', 'global markets',
                            'energy', 'oil', 'gas', 'renewable energy', 'nuclear energy',
                            'environment', 'pollution', 'biodiversity', 'deforestation', 'water crisis',
                            'migration', 'refugees', 'immigration', 'border security',
                            'terrorism', 'extremism', 'security', 'military', 'defense',
                            'education', 'research', 'innovation', 'space exploration',
                            'food security', 'agriculture', 'hunger', 'poverty', 'development',
                            'infrastructure', 'transportation', 'urbanization', 'housing',
                            'finance', 'banking', 'cryptocurrency', 'stock market', 'investment',
                            'social media', 'disinformation', 'privacy', 'data protection',
                            'culture', 'arts', 'sports', 'entertainment', 'tourism'
                        ],
                        help='Keywords to search for')
    return parser.parse_args()

def load_themes(themes_file):
    """Load themes from a JSONL file"""
    themes = []
    try:
        with open(themes_file, 'r') as f:
            for line in f:
                theme = json.loads(line)
                themes.append(theme)
    except FileNotFoundError:
        logger.warning(f"Themes file {themes_file} not found. Using default themes.")
        # Default themes if file not found
        themes = [
            {"theme": "ECON", "description": "Economy"},
            {"theme": "ENV", "description": "Environment"},
            {"theme": "TECH", "description": "Technology"},
            {"theme": "HEALTH", "description": "Health"},
            {"theme": "CONFLICT", "description": "Conflict"},
            {"theme": "POLITICAL", "description": "Politics"}
        ]
    return themes

def setup_database(db_path):
    """Set up SQLite database for deduplication and incremental fetching"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create tables if they don't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS articles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT UNIQUE,
        title TEXT,
        content_hash TEXT,
        seendate TEXT,
        fetch_date TEXT,
        language TEXT,
        domain TEXT,
        sourcecountry TEXT,
        theme_id TEXT,
        theme_description TEXT
    )
    ''')
    
    # Create index on url for faster lookups
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_articles_url ON articles(url)')
    
    # Create index on content_hash for faster deduplication
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_articles_content_hash ON articles(content_hash)')
    
    conn.commit()
    return conn

def compute_content_hash(article):
    """Compute a hash of the article content for deduplication"""
    # Combine title and URL for a more robust hash
    content = f"{article.get('title', '')}{article.get('url', '')}"
    return hashlib.md5(content.encode('utf-8')).hexdigest()

def is_duplicate(conn, article):
    """Check if an article is a duplicate based on URL or content hash"""
    cursor = conn.cursor()
    
    # Check if URL already exists
    url = article.get('url', '')
    cursor.execute('SELECT id FROM articles WHERE url = ?', (url,))
    if cursor.fetchone():
        return True
    
    # Check if content hash already exists
    content_hash = compute_content_hash(article)
    cursor.execute('SELECT id FROM articles WHERE content_hash = ?', (content_hash,))
    if cursor.fetchone():
        return True
    
    return False

def normalize_url(url):
    """Normalize URL to avoid duplicates with different query parameters"""
    parsed = urlparse(url)
    # Return the URL without query parameters and fragments
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

def fetch_articles_for_keyword(keyword, languages, timespan, max_articles_per_keyword, delay, conn=None):
    """
    Fetch articles for a specific keyword in multiple languages with deduplication
    
    Args:
        keyword: Keyword to search for
        languages: List of languages to fetch
        timespan: Timespan for fetching articles (e.g., "1m" for 1 month)
        max_articles_per_keyword: Maximum number of articles per keyword and language
        delay: Delay between API calls to avoid rate limiting
        conn: SQLite connection for deduplication
        
    Returns:
        DataFrame of articles
    """
    all_articles = pd.DataFrame()
    
    for language in languages:
        logger.info(f"  - Language: {language}")
        
        try:
            # Initialize GDELT client
            client = GdeltDoc()
            
            # Create filters for keyword search
            filters = Filters(
                keyword=keyword,
                language=language,
                timespan=timespan,
                num_records=max_articles_per_keyword
            )
            
            # Fetch articles
            articles = client.article_search(filters)
            
            # Add keyword and language information
            if not articles.empty:
                articles['keyword'] = keyword
                articles['target_language'] = language
                
                # Add content hash for deduplication
                articles['content_hash'] = articles.apply(compute_content_hash, axis=1)
                
                # Normalize URLs
                articles['url'] = articles['url'].apply(normalize_url)
                
                # Deduplicate based on URL and content hash
                if conn:
                    # Filter out duplicates
                    original_count = len(articles)
                    articles = articles[~articles.apply(lambda x: is_duplicate(conn, x), axis=1)]
                    duplicate_count = original_count - len(articles)
                    
                    if duplicate_count > 0:
                        logger.info(f"    - Filtered out {duplicate_count} duplicate articles")
                
                # Count articles
                logger.info(f"    - Found {len(articles)} {language} articles")
                
                # Add to all articles
                all_articles = pd.concat([all_articles, articles], ignore_index=True)
                
                # Store new articles in database if connection provided
                if conn and not articles.empty:
                    cursor = conn.cursor()
                    fetch_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    
                    for _, article in articles.iterrows():
                        cursor.execute('''
                        INSERT OR IGNORE INTO articles 
                        (url, title, content_hash, seendate, fetch_date, language, domain, sourcecountry, theme_id, theme_description)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            article.get('url', ''),
                            article.get('title', ''),
                            article.get('content_hash', ''),
                            article.get('seendate', ''),
                            fetch_date,
                            article.get('language', ''),
                            article.get('domain', ''),
                            article.get('sourcecountry', ''),
                            article.get('theme_id', ''),
                            article.get('theme_description', '')
                        ))
                    
                    conn.commit()
            
            # Add a delay to avoid rate limiting
            time.sleep(delay + random.random())
            
        except Exception as e:
            logger.error(f"    - Error fetching {language} articles for '{keyword}': {e}")
            continue
    
    return all_articles

def fetch_articles_for_theme(theme_id, theme_description, languages, timespan, max_articles_per_theme, delay, conn=None):
    """
    Fetch articles for a specific theme in multiple languages with deduplication
    
    Args:
        theme_id: Theme ID
        theme_description: Theme description
        languages: List of languages to fetch
        timespan: Timespan for fetching articles (e.g., "1m" for 1 month)
        max_articles_per_theme: Maximum number of articles per theme and language
        delay: Delay between API calls to avoid rate limiting
        conn: SQLite connection for deduplication
        
    Returns:
        DataFrame of articles
    """
    all_articles = pd.DataFrame()
    
    # Use the theme ID as a keyword search
    # This is more reliable than using the theme parameter
    keyword = theme_id.replace("_", " ").lower()
    
    logger.info(f"Fetching articles for theme '{theme_id}' ({theme_description})")
    
    for language in languages:
        logger.info(f"  - Language: {language}")
        
        try:
            # Initialize GDELT client
            client = GdeltDoc()
            
            # Create filters for keyword search
            filters = Filters(
                keyword=keyword,
                language=language,
                timespan=timespan,
                num_records=max_articles_per_theme
            )
            
            # Fetch articles
            articles = client.article_search(filters)
            
            # Add theme and language information
            if not articles.empty:
                articles['theme_id'] = theme_id
                articles['theme_description'] = theme_description
                articles['target_language'] = language
                
                # Add content hash for deduplication
                articles['content_hash'] = articles.apply(compute_content_hash, axis=1)
                
                # Normalize URLs
                articles['url'] = articles['url'].apply(normalize_url)
                
                # Deduplicate based on URL and content hash
                if conn:
                    # Filter out duplicates
                    original_count = len(articles)
                    articles = articles[~articles.apply(lambda x: is_duplicate(conn, x), axis=1)]
                    duplicate_count = original_count - len(articles)
                    
                    if duplicate_count > 0:
                        logger.info(f"    - Filtered out {duplicate_count} duplicate articles")
                
                # Count articles
                logger.info(f"    - Found {len(articles)} {language} articles")
                
                # Add to all articles
                all_articles = pd.concat([all_articles, articles], ignore_index=True)
                
                # Store new articles in database if connection provided
                if conn and not articles.empty:
                    cursor = conn.cursor()
                    fetch_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    
                    for _, article in articles.iterrows():
                        cursor.execute('''
                        INSERT OR IGNORE INTO articles 
                        (url, title, content_hash, seendate, fetch_date, language, domain, sourcecountry, theme_id, theme_description)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            article.get('url', ''),
                            article.get('title', ''),
                            article.get('content_hash', ''),
                            article.get('seendate', ''),
                            fetch_date,
                            article.get('language', ''),
                            article.get('domain', ''),
                            article.get('sourcecountry', ''),
                            theme_id,
                            theme_description
                        ))
                    
                    conn.commit()
            
            # Add a delay to avoid rate limiting
            time.sleep(delay + random.random())
            
        except Exception as e:
            logger.error(f"    - Error fetching {language} articles for theme '{theme_id}': {e}")
            continue
    
    return all_articles

def save_chunk(articles_df, chunk_num, output_dir):
    """Save a chunk of articles to CSV"""
    # Create chunks directory if it doesn't exist
    chunks_dir = os.path.join(output_dir, 'chunks')
    os.makedirs(chunks_dir, exist_ok=True)
    
    # Save chunk to CSV
    chunk_file = os.path.join(chunks_dir, f'articles_chunk_{chunk_num}.csv')
    articles_df.to_csv(chunk_file, index=False)
    logger.info(f"Saved chunk {chunk_num} with {len(articles_df)} articles to {chunk_file}")
    
    return chunk_file

def merge_chunks(output_dir):
    """Merge all chunks into a single CSV file with deduplication"""
    # Get all chunk files
    chunks_dir = os.path.join(output_dir, 'chunks')
    chunk_files = [os.path.join(chunks_dir, f) for f in os.listdir(chunks_dir) if f.startswith('articles_chunk_') and f.endswith('.csv')]
    
    if not chunk_files:
        logger.warning("No chunk files found to merge")
        return pd.DataFrame()
    
    # Merge all chunks
    all_articles = pd.DataFrame()
    
    for chunk_file in tqdm(chunk_files, desc="Merging chunks"):
        try:
            chunk = pd.read_csv(chunk_file)
            all_articles = pd.concat([all_articles, chunk], ignore_index=True)
        except Exception as e:
            logger.error(f"Error reading chunk file {chunk_file}: {e}")
    
    # Remove duplicates
    logger.info(f"Total articles before deduplication: {len(all_articles)}")
    
    # First deduplicate by URL
    all_articles = all_articles.drop_duplicates(subset=['url'])
    logger.info(f"Articles after URL deduplication: {len(all_articles)}")
    
    # Then deduplicate by content hash if available
    if 'content_hash' in all_articles.columns:
        all_articles = all_articles.drop_duplicates(subset=['content_hash'])
        logger.info(f"Articles after content hash deduplication: {len(all_articles)}")
    
    # Finally deduplicate by title similarity (optional, can be expensive)
    # This is a simple approach - for more advanced deduplication, consider using
    # text similarity measures like cosine similarity with TF-IDF vectors
    
    # Save merged file
    merged_file = os.path.join(output_dir, 'all_articles.csv')
    all_articles.to_csv(merged_file, index=False)
    logger.info(f"Saved {len(all_articles)} articles to {merged_file}")
    
    return all_articles

def get_existing_article_count(conn):
    """Get the count of existing articles in the database"""
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM articles')
    return cursor.fetchone()[0]

def main():
    """Main function"""
    args = parse_args()
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Set up database for deduplication and incremental fetching
    db_path = args.db_path or os.path.join(args.output_dir, 'articles.db')
    conn = setup_database(db_path)
    
    # Get existing article count if incremental
    existing_count = 0
    if args.incremental:
        existing_count = get_existing_article_count(conn)
        logger.info(f"Found {existing_count} existing articles in database")
    
    # Load themes
    themes = load_themes(args.themes_file)
    logger.info(f"Loaded {len(themes)} themes")
    
    # Calculate articles per keyword and theme
    total_sources = len(args.keywords) + len(themes)
    articles_per_source = max(10, args.max_articles // total_sources)
    
    # Split keywords into chunks to avoid memory issues
    keyword_chunks = [args.keywords[i:i+10] for i in range(0, len(args.keywords), 10)]
    
    # Fetch articles for each keyword chunk
    chunk_num = 0
    successful_keywords = 0
    
    for keyword_chunk in tqdm(keyword_chunks, desc="Fetching keyword chunks"):
        chunk_articles = pd.DataFrame()
        
        for keyword in tqdm(keyword_chunk, desc=f"Fetching keywords in chunk {chunk_num+1}"):
            # Fetch articles for this keyword
            articles = fetch_articles_for_keyword(
                keyword,
                args.languages,
                args.timespan,
                articles_per_source,
                args.delay,
                conn
            )
            
            # Add to chunk articles
            if not articles.empty:
                chunk_articles = pd.concat([chunk_articles, articles], ignore_index=True)
                successful_keywords += 1
            
            # Add a delay to avoid rate limiting
            time.sleep(args.delay + random.random())
        
        # Save this chunk if it has articles
        if not chunk_articles.empty:
            save_chunk(chunk_articles, chunk_num, args.output_dir)
            chunk_num += 1
    
    logger.info(f"Fetched articles for {successful_keywords} out of {len(args.keywords)} keywords")
    
    # Split themes into chunks to avoid memory issues
    theme_chunks = [themes[i:i+10] for i in range(0, len(themes), 10)]
    
    # Fetch articles for each theme chunk
    successful_themes = 0
    
    for theme_chunk in tqdm(theme_chunks, desc="Fetching theme chunks"):
        chunk_articles = pd.DataFrame()
        
        for theme in tqdm(theme_chunk, desc=f"Fetching themes in chunk {chunk_num+1}"):
            theme_id = theme['theme']
            theme_description = theme['description']
            
            # Fetch articles for this theme
            articles = fetch_articles_for_theme(
                theme_id,
                theme_description,
                args.languages,
                args.timespan,
                articles_per_source,
                args.delay,
                conn
            )
            
            # Add to chunk articles
            if not articles.empty:
                chunk_articles = pd.concat([chunk_articles, articles], ignore_index=True)
                successful_themes += 1
            
            # Add a delay to avoid rate limiting
            time.sleep(args.delay + random.random())
        
        # Save this chunk if it has articles
        if not chunk_articles.empty:
            save_chunk(chunk_articles, chunk_num, args.output_dir)
            chunk_num += 1
    
    logger.info(f"Fetched articles for {successful_themes} out of {len(themes)} themes")
    
    # Merge all chunks
    all_articles = merge_chunks(args.output_dir)
    
    # Save themes to JSON
    themes_file = os.path.join(args.output_dir, 'themes.json')
    with open(themes_file, 'w') as f:
        json.dump(themes, f, indent=2)
    logger.info(f"Saved {len(themes)} themes to {themes_file}")
    
    # Get final article count from database
    final_count = get_existing_article_count(conn)
    new_articles = final_count - existing_count
    
    # Save summary to JSON
    summary = {
        'total_articles': len(all_articles),
        'total_articles_in_db': final_count,
        'new_articles_added': new_articles,
        'timespan': args.timespan,
        'languages': args.languages,
        'keywords': args.keywords,
        'themes': [theme['theme'] for theme in themes],
        'fetch_date': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'incremental': args.incremental
    }
    
    summary_file = os.path.join(args.output_dir, 'summary.json')
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    logger.info(f"Saved summary to {summary_file}")
    
    # Close database connection
    conn.close()
    
    logger.info(f"Dataset saved to {args.output_dir}")
    logger.info(f"Added {new_articles} new articles to the database")

if __name__ == "__main__":
    main()
