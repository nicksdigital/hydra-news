#!/usr/bin/env python3
"""
GDELT Data Integration Script

This script integrates the GDELT dataset with the Hydra News system by:
1. Converting GDELT articles to Hydra News content format
2. Processing the content through the Hydra News content processor
3. Storing the processed content in the Hydra News database
"""

import os
import sys
import json
import pandas as pd
from datetime import datetime
import hashlib
import argparse
import logging

# Add the Hydra News Python source directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'python/src')))

# Import Hydra News modules
try:
    from content_processor import ContentProcessor, NewsContent
    from content_processor_service import ContentProcessorService
except ImportError:
    print("Error: Could not import Hydra News modules. Make sure you're running this script from the Hydra News root directory.")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("gdelt_integration.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("gdelt_integration")

def load_gdelt_dataset(dataset_path):
    """Load the GDELT dataset from CSV"""
    logger.info(f"Loading GDELT dataset from {dataset_path}")
    try:
        articles_df = pd.read_csv(dataset_path)
        logger.info(f"Loaded {len(articles_df)} articles")
        return articles_df
    except Exception as e:
        logger.error(f"Error loading dataset: {e}")
        return None

def convert_to_hydra_format(article, theme_map):
    """Convert a GDELT article to Hydra News content format"""
    try:
        # Create a unique content hash
        content_hash = hashlib.sha256(f"{article['url']}:{article['title']}".encode()).hexdigest()
        
        # Convert seendate to datetime
        if isinstance(article['seendate'], str):
            publish_date = datetime.strptime(article['seendate'], '%Y-%m-%d %H:%M:%S')
        else:
            publish_date = article['seendate']
        
        # Create NewsContent object
        news_content = NewsContent(
            title=article['title'],
            content=f"[This content was extracted from {article['url']}]",  # Placeholder for actual content
            source=article['domain'],
            url=article['url'],
            author="Unknown",  # GDELT doesn't provide author information
            publish_date=publish_date
        )
        
        # Set content hash
        news_content.content_hash = content_hash
        
        # Add theme information as metadata
        news_content.metadata = {
            "theme_id": article['theme_id'],
            "theme_description": theme_map.get(article['theme_id'], "Unknown"),
            "language": article['language'],
            "source_country": article['sourcecountry'],
            "gdelt_source": True
        }
        
        return news_content
    except Exception as e:
        logger.error(f"Error converting article to Hydra format: {e}")
        return None

def process_content(content_processor, news_content):
    """Process content through the Hydra News content processor"""
    try:
        # Process the content
        processed_content = content_processor.process_content(news_content)
        return processed_content
    except Exception as e:
        logger.error(f"Error processing content: {e}")
        return None

def store_content(processed_content, output_dir):
    """Store processed content in JSON format"""
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Create a filename based on content hash
        filename = os.path.join(output_dir, f"{processed_content.content_hash}.json")
        
        # Convert to dictionary
        content_dict = processed_content.to_dict()
        
        # Save to JSON file
        with open(filename, 'w') as f:
            json.dump(content_dict, f, indent=2)
        
        return filename
    except Exception as e:
        logger.error(f"Error storing content: {e}")
        return None

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Integrate GDELT dataset with Hydra News")
    parser.add_argument("--dataset", default="dataset_6months/all_articles.csv", help="Path to GDELT dataset CSV")
    parser.add_argument("--themes", default="dataset_6months/themes.json", help="Path to themes JSON file")
    parser.add_argument("--output", default="hydra_content", help="Output directory for processed content")
    parser.add_argument("--limit", type=int, default=100, help="Limit the number of articles to process")
    args = parser.parse_args()
    
    # Load the dataset
    articles_df = load_gdelt_dataset(args.dataset)
    if articles_df is None:
        return
    
    # Load theme map
    try:
        with open(args.themes, 'r') as f:
            theme_map = json.load(f)
    except Exception as e:
        logger.error(f"Error loading theme map: {e}")
        return
    
    # Initialize content processor
    logger.info("Initializing Hydra News content processor")
    content_processor = ContentProcessor()
    
    # Process articles
    logger.info(f"Processing up to {args.limit} articles")
    processed_count = 0
    error_count = 0
    
    # Limit the number of articles to process
    if args.limit > 0:
        articles_df = articles_df.head(args.limit)
    
    for _, article in articles_df.iterrows():
        try:
            # Convert to Hydra format
            news_content = convert_to_hydra_format(article, theme_map)
            if news_content is None:
                error_count += 1
                continue
            
            # Process content
            processed_content = process_content(content_processor, news_content)
            if processed_content is None:
                error_count += 1
                continue
            
            # Store content
            filename = store_content(processed_content, args.output)
            if filename is None:
                error_count += 1
                continue
            
            processed_count += 1
            if processed_count % 10 == 0:
                logger.info(f"Processed {processed_count} articles")
        
        except Exception as e:
            logger.error(f"Error processing article: {e}")
            error_count += 1
    
    logger.info(f"Processing complete. Processed {processed_count} articles with {error_count} errors.")
    logger.info(f"Processed content stored in {args.output}")

if __name__ == "__main__":
    main()
