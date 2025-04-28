#!/usr/bin/env python3
"""
GDELT Theme Analyzer

This module provides functions for analyzing themes in GDELT news data.
"""

import pandas as pd
import numpy as np
from collections import Counter
import logging

# Set up logging
logger = logging.getLogger(__name__)

def analyze_themes(articles, themes):
    """
    Analyze theme distribution

    Args:
        articles: DataFrame containing articles
        themes: Dictionary or list mapping theme IDs to descriptions

    Returns:
        DataFrame with theme counts and descriptions
    """
    logger.info("Analyzing theme distribution")

    # Count articles per theme
    theme_counts = articles['theme_id'].value_counts().reset_index()
    theme_counts.columns = ['theme_id', 'count']

    # Create a themes map dictionary if themes is a list
    if isinstance(themes, list):
        themes_map = {theme['theme']: theme['description'] for theme in themes}
    else:
        themes_map = themes

    # Add theme description
    theme_counts['description'] = theme_counts['theme_id'].map(themes_map)

    logger.info(f"Found {len(theme_counts)} themes")
    return theme_counts

def analyze_theme_by_language(articles):
    """
    Analyze theme distribution by language

    Args:
        articles: DataFrame containing articles

    Returns:
        Dictionary mapping languages to theme count DataFrames
    """
    logger.info("Analyzing theme distribution by language")

    # Get unique languages
    languages = articles['language'].unique()

    # Analyze themes for each language
    language_themes = {}
    for language in languages:
        language_articles = articles[articles['language'] == language]

        # Count articles per theme
        theme_counts = language_articles['theme_id'].value_counts().reset_index()
        theme_counts.columns = ['theme_id', 'count']

        # Add theme description
        theme_counts['description'] = theme_counts['theme_id'].map(
            lambda x: language_articles[language_articles['theme_id'] == x]['theme_description'].iloc[0]
            if not language_articles[language_articles['theme_id'] == x].empty else None
        )

        language_themes[language] = theme_counts
        logger.info(f"Found {len(theme_counts)} themes for language '{language}'")

    return language_themes

def analyze_theme_correlations(articles, top_n=15):
    """
    Analyze correlations between themes

    Args:
        articles: DataFrame containing articles
        top_n: Number of top themes to analyze

    Returns:
        Correlation matrix for top themes
    """
    logger.info(f"Analyzing correlations between top {top_n} themes")

    # Get top themes
    top_themes = articles['theme_id'].value_counts().head(top_n).index.tolist()

    # Create a binary matrix of articles x themes
    theme_matrix = pd.DataFrame(index=articles.index)
    for theme in top_themes:
        theme_matrix[theme] = (articles['theme_id'] == theme).astype(int)

    # Calculate correlation
    theme_corr = theme_matrix.corr()

    logger.info(f"Generated {len(theme_corr)} x {len(theme_corr)} correlation matrix")
    return theme_corr

def analyze_theme_trends_over_time(articles):
    """
    Analyze theme trends over time

    Args:
        articles: DataFrame containing articles

    Returns:
        DataFrame with theme counts by date
    """
    logger.info("Analyzing theme trends over time")

    # Group by date and theme
    theme_date_counts = articles.groupby(['date', 'theme_id']).size().reset_index(name='count')

    # Pivot to get themes as columns
    theme_trends = theme_date_counts.pivot(index='date', columns='theme_id', values='count')

    # Fill NaN with 0
    theme_trends = theme_trends.fillna(0)

    logger.info(f"Generated theme trends for {len(theme_trends.columns)} themes over {len(theme_trends)} dates")
    return theme_trends

def get_theme_co_occurrences(articles, min_count=2):
    """
    Find co-occurrences of themes in the same articles

    Args:
        articles: DataFrame containing articles
        min_count: Minimum number of co-occurrences to include

    Returns:
        DataFrame with theme co-occurrence counts
    """
    logger.info("Analyzing theme co-occurrences")

    # Group articles by URL to find duplicates with different themes
    url_groups = articles.groupby('url')['theme_id'].apply(list)

    # Count co-occurrences
    co_occurrences = []
    for themes in url_groups:
        if len(themes) > 1:
            # Get unique themes
            unique_themes = list(set(themes))

            # Add all pairs of themes
            for i in range(len(unique_themes)):
                for j in range(i+1, len(unique_themes)):
                    co_occurrences.append((unique_themes[i], unique_themes[j]))

    # Count occurrences of each pair
    co_occurrence_counts = Counter(co_occurrences)

    # Convert to DataFrame
    co_df = pd.DataFrame([
        {'theme1': t1, 'theme2': t2, 'count': count}
        for (t1, t2), count in co_occurrence_counts.items()
        if count >= min_count
    ])

    # Sort by count
    if not co_df.empty:
        co_df = co_df.sort_values('count', ascending=False)

    logger.info(f"Found {len(co_df)} theme co-occurrences with count >= {min_count}")
    return co_df
