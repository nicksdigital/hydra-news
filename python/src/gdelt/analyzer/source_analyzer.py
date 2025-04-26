#!/usr/bin/env python3
"""
GDELT Source Analyzer

This module provides functions for analyzing sources in GDELT news data.
"""

import pandas as pd
import numpy as np
from collections import Counter
import logging

# Set up logging
logger = logging.getLogger(__name__)

def analyze_domains(articles):
    """
    Analyze domain distribution
    
    Args:
        articles: DataFrame containing articles
        
    Returns:
        Tuple of (domain_counts, tld_counts)
    """
    logger.info("Analyzing domain distribution")
    
    # Top domains
    domain_counts = articles['domain'].value_counts().head(20)
    logger.info(f"Analyzed top {len(domain_counts)} domains")
    
    # Top TLDs
    tld_counts = articles['tld'].value_counts().head(10)
    logger.info(f"Analyzed top {len(tld_counts)} TLDs")
    
    return domain_counts, tld_counts

def analyze_languages(articles):
    """
    Analyze language distribution
    
    Args:
        articles: DataFrame containing articles
        
    Returns:
        Series with language counts
    """
    logger.info("Analyzing language distribution")
    
    # Language counts
    language_counts = articles['language'].value_counts().head(10)
    logger.info(f"Analyzed top {len(language_counts)} languages")
    
    return language_counts

def analyze_countries(articles):
    """
    Analyze source country distribution
    
    Args:
        articles: DataFrame containing articles
        
    Returns:
        Series with country counts
    """
    logger.info("Analyzing source country distribution")
    
    # Country counts
    country_counts = articles['sourcecountry'].value_counts().head(15)
    logger.info(f"Analyzed top {len(country_counts)} countries")
    
    return country_counts

def analyze_domain_by_theme(articles):
    """
    Analyze domain distribution by theme
    
    Args:
        articles: DataFrame containing articles
        
    Returns:
        Dictionary mapping themes to domain count DataFrames
    """
    logger.info("Analyzing domain distribution by theme")
    
    # Get unique themes
    themes = articles['theme_id'].unique()
    
    # Analyze domains for each theme
    theme_domains = {}
    for theme in themes:
        theme_articles = articles[articles['theme_id'] == theme]
        
        # Count articles per domain
        domain_counts = theme_articles['domain'].value_counts().head(10)
        
        theme_domains[theme] = domain_counts
        logger.info(f"Found {len(domain_counts)} domains for theme '{theme}'")
    
    return theme_domains

def analyze_domain_language_matrix(articles):
    """
    Create a matrix of domains by languages
    
    Args:
        articles: DataFrame containing articles
        
    Returns:
        DataFrame with domains as rows and languages as columns
    """
    logger.info("Creating domain-language matrix")
    
    # Get top domains and languages
    top_domains = articles['domain'].value_counts().head(20).index
    top_languages = articles['language'].value_counts().head(10).index
    
    # Filter articles to top domains and languages
    filtered = articles[
        articles['domain'].isin(top_domains) & 
        articles['language'].isin(top_languages)
    ]
    
    # Create the matrix
    domain_lang_matrix = pd.crosstab(
        filtered['domain'], 
        filtered['language'],
        normalize='index'  # Normalize by row (domain)
    )
    
    logger.info(f"Created {len(domain_lang_matrix)} x {len(domain_lang_matrix.columns)} domain-language matrix")
    return domain_lang_matrix

def analyze_source_diversity(articles):
    """
    Analyze the diversity of sources
    
    Args:
        articles: DataFrame containing articles
        
    Returns:
        Dictionary with diversity metrics
    """
    logger.info("Analyzing source diversity")
    
    # Calculate diversity metrics
    total_articles = len(articles)
    unique_domains = len(articles['domain'].unique())
    unique_countries = len(articles['sourcecountry'].unique())
    unique_languages = len(articles['language'].unique())
    
    # Calculate concentration metrics (Herfindahl-Hirschman Index)
    domain_shares = articles['domain'].value_counts() / total_articles
    domain_hhi = (domain_shares ** 2).sum()
    
    country_shares = articles['sourcecountry'].value_counts() / total_articles
    country_hhi = (country_shares ** 2).sum()
    
    language_shares = articles['language'].value_counts() / total_articles
    language_hhi = (language_shares ** 2).sum()
    
    # Create diversity metrics dictionary
    diversity = {
        'total_articles': total_articles,
        'unique_domains': unique_domains,
        'unique_countries': unique_countries,
        'unique_languages': unique_languages,
        'domain_concentration': domain_hhi,
        'country_concentration': country_hhi,
        'language_concentration': language_hhi,
        'domain_diversity': 1 - domain_hhi,
        'country_diversity': 1 - country_hhi,
        'language_diversity': 1 - language_hhi
    }
    
    logger.info(f"Calculated diversity metrics: {diversity}")
    return diversity
