#!/usr/bin/env python3
"""
GDELT Data Loader

This module provides functions for loading and preprocessing GDELT news data.
"""

import os
import json
import pandas as pd
from datetime import datetime
import logging

# Set up logging
logger = logging.getLogger(__name__)

def load_dataset(dataset_dir="dataset_gdelt_month"):
    """
    Load the dataset from CSV and JSON files
    
    Args:
        dataset_dir: Directory containing the dataset files
        
    Returns:
        Tuple of (articles DataFrame, themes dictionary, summary dictionary)
    """
    logger.info(f"Loading dataset from {dataset_dir}")
    
    # Load all articles
    articles_path = os.path.join(dataset_dir, "all_articles.csv")
    if not os.path.exists(articles_path):
        raise FileNotFoundError(f"Articles file not found: {articles_path}")
    
    articles = pd.read_csv(articles_path)
    logger.info(f"Loaded {len(articles)} articles from {articles_path}")

    # Load theme information
    themes_path = os.path.join(dataset_dir, "themes.json")
    if not os.path.exists(themes_path):
        raise FileNotFoundError(f"Themes file not found: {themes_path}")
    
    with open(themes_path, 'r') as f:
        themes = json.load(f)
    logger.info(f"Loaded {len(themes)} themes from {themes_path}")

    # Load summary
    summary_path = os.path.join(dataset_dir, "summary.json")
    if not os.path.exists(summary_path):
        raise FileNotFoundError(f"Summary file not found: {summary_path}")
    
    with open(summary_path, 'r') as f:
        summary = json.load(f)
    logger.info(f"Loaded summary from {summary_path}")

    return articles, themes, summary

def preprocess_articles(articles, themes_map):
    """
    Preprocess the articles dataframe
    
    Args:
        articles: DataFrame containing articles
        themes_map: Dictionary mapping theme IDs to descriptions
        
    Returns:
        Preprocessed articles DataFrame
    """
    logger.info("Preprocessing articles")
    
    # Make a copy to avoid modifying the original
    df = articles.copy()
    
    # Convert seendate to datetime
    df['seendate'] = pd.to_datetime(df['seendate'])

    # Extract date components
    df['date'] = df['seendate'].dt.date
    df['hour'] = df['seendate'].dt.hour
    df['day_of_week'] = df['seendate'].dt.day_name()
    df['month'] = df['seendate'].dt.month
    df['year'] = df['seendate'].dt.year

    # Add theme description
    df['theme_description'] = df['theme_id'].map(themes_map)

    # Extract top-level domain
    df['tld'] = df['domain'].apply(lambda x: x.split('.')[-1] if pd.notna(x) else None)
    
    # Clean title text (remove None values)
    df['title'] = df['title'].fillna('')
    
    # Create a clean URL column (remove None values)
    df['clean_url'] = df['url'].fillna('')
    
    logger.info("Preprocessing complete")
    return df

def save_processed_data(articles, output_dir="processed_gdelt"):
    """
    Save the processed data to CSV
    
    Args:
        articles: Processed articles DataFrame
        output_dir: Directory to save the processed data
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Save processed articles
    output_path = os.path.join(output_dir, "processed_articles.csv")
    articles.to_csv(output_path, index=False)
    logger.info(f"Saved processed articles to {output_path}")
    
    return output_path
