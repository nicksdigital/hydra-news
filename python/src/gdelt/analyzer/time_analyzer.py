#!/usr/bin/env python3
"""
GDELT Time Analyzer

This module provides functions for analyzing time patterns in GDELT news data.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

# Set up logging
logger = logging.getLogger(__name__)

def analyze_time_patterns(articles):
    """
    Analyze time patterns in the articles
    
    Args:
        articles: DataFrame containing articles
        
    Returns:
        Tuple of (date_counts, hour_counts, day_counts)
    """
    logger.info("Analyzing time patterns")
    
    # Articles by date
    date_counts = articles['date'].value_counts().sort_index()
    logger.info(f"Analyzed articles by date ({len(date_counts)} dates)")
    
    # Articles by hour of day
    hour_counts = articles['hour'].value_counts().sort_index()
    logger.info(f"Analyzed articles by hour ({len(hour_counts)} hours)")
    
    # Articles by day of week
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    day_counts = articles['day_of_week'].value_counts()
    day_counts = day_counts.reindex(day_order)
    logger.info(f"Analyzed articles by day of week ({len(day_counts)} days)")
    
    return date_counts, hour_counts, day_counts

def analyze_publication_delay(articles):
    """
    Analyze the delay between events and their publication
    
    Args:
        articles: DataFrame containing articles
        
    Returns:
        DataFrame with publication delay statistics
    """
    logger.info("Analyzing publication delay")
    
    # Check if we have the necessary columns
    if 'seendate' not in articles.columns:
        logger.warning("seendate column not found, skipping publication delay analysis")
        return None
    
    # Calculate publication delay statistics by theme
    delay_stats = []
    
    for theme_id in articles['theme_id'].unique():
        theme_articles = articles[articles['theme_id'] == theme_id]
        
        # Get the first and last publication dates
        first_date = theme_articles['seendate'].min()
        last_date = theme_articles['seendate'].max()
        
        # Calculate the time span
        time_span = (last_date - first_date).total_seconds() / 3600  # in hours
        
        # Calculate the average publication rate (articles per day)
        num_articles = len(theme_articles)
        days_span = time_span / 24
        if days_span > 0:
            articles_per_day = num_articles / days_span
        else:
            articles_per_day = num_articles
        
        delay_stats.append({
            'theme_id': theme_id,
            'theme_description': theme_articles['theme_description'].iloc[0],
            'first_date': first_date,
            'last_date': last_date,
            'time_span_hours': time_span,
            'num_articles': num_articles,
            'articles_per_day': articles_per_day
        })
    
    # Convert to DataFrame
    delay_df = pd.DataFrame(delay_stats)
    
    # Sort by articles per day
    delay_df = delay_df.sort_values('articles_per_day', ascending=False)
    
    logger.info(f"Analyzed publication delay for {len(delay_df)} themes")
    return delay_df

def analyze_time_series(articles, freq='D'):
    """
    Analyze time series of article counts
    
    Args:
        articles: DataFrame containing articles
        freq: Frequency for resampling ('D' for daily, 'H' for hourly, etc.)
        
    Returns:
        DataFrame with time series data
    """
    logger.info(f"Analyzing time series with frequency '{freq}'")
    
    # Convert to datetime index
    ts_df = articles.set_index('seendate').copy()
    
    # Resample to get counts
    ts_counts = ts_df.resample(freq).size()
    
    # Create a DataFrame with the counts
    ts_data = pd.DataFrame({'count': ts_counts})
    
    # Add moving averages
    ts_data['ma_3'] = ts_data['count'].rolling(window=3).mean()
    ts_data['ma_7'] = ts_data['count'].rolling(window=7).mean()
    
    logger.info(f"Generated time series with {len(ts_data)} data points")
    return ts_data

def detect_time_anomalies(time_series, window=7, threshold=2.0):
    """
    Detect anomalies in the time series
    
    Args:
        time_series: DataFrame with time series data
        window: Window size for rolling statistics
        threshold: Threshold for anomaly detection (in standard deviations)
        
    Returns:
        DataFrame with anomalies
    """
    logger.info(f"Detecting time anomalies with window={window}, threshold={threshold}")
    
    # Calculate rolling mean and standard deviation
    rolling_mean = time_series['count'].rolling(window=window).mean()
    rolling_std = time_series['count'].rolling(window=window).std()
    
    # Calculate z-scores
    z_scores = (time_series['count'] - rolling_mean) / rolling_std
    
    # Identify anomalies
    anomalies = time_series[abs(z_scores) > threshold].copy()
    anomalies['z_score'] = z_scores[abs(z_scores) > threshold]
    
    logger.info(f"Detected {len(anomalies)} anomalies")
    return anomalies
