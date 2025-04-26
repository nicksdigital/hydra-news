#!/usr/bin/env python3
"""
GDELT Trust Scorer

This module provides functions for calculating trust scores for GDELT news articles and entities.
"""

import pandas as pd
import numpy as np
import logging
from collections import defaultdict

# Set up logging
logger = logging.getLogger(__name__)

class TrustScorer:
    """Class for calculating trust scores for articles and entities"""
    
    def __init__(self, db_manager=None):
        """
        Initialize the trust scorer
        
        Args:
            db_manager: DatabaseManager instance for accessing stored data
        """
        self.db_manager = db_manager
        self.domain_trust_scores = {}
        self.country_trust_scores = {}
        self.theme_trust_scores = {}
        
        # Load domain trust scores from database if available
        if db_manager and db_manager.conn:
            try:
                sources_df = db_manager.get_source_stats(limit=1000)
                for _, row in sources_df.iterrows():
                    self.domain_trust_scores[row['domain']] = row['trust_score']
                logger.info(f"Loaded trust scores for {len(self.domain_trust_scores)} domains")
            except Exception as e:
                logger.error(f"Error loading domain trust scores: {e}")
    
    def score_articles(self, articles_df):
        """
        Calculate trust scores for articles
        
        Args:
            articles_df: DataFrame containing articles
            
        Returns:
            DataFrame with added trust scores
        """
        logger.info("Calculating trust scores for articles")
        
        # Make a copy of the DataFrame
        df = articles_df.copy()
        
        # Initialize trust scores
        df['trust_score'] = 0.5
        
        # 1. Domain-based trust
        df['domain_trust'] = df['domain'].map(self.domain_trust_scores).fillna(0.5)
        
        # 2. Country-based trust (some countries have more reliable media)
        country_factors = {
            'US': 0.1,
            'GB': 0.1,
            'CA': 0.1,
            'AU': 0.1,
            'FR': 0.1,
            'DE': 0.1,
            'JP': 0.1,
            'KR': 0.1,
            'SG': 0.1,
            'NZ': 0.1
        }
        df['country_factor'] = df['sourcecountry'].map(country_factors).fillna(0)
        
        # 3. Theme-based trust (some themes are more factual)
        theme_factors = {
            'SCIENCE': 0.1,
            'EDUCATION': 0.05,
            'MEDICAL': 0.05,
            'LEGISLATION': 0.05,
            'TRIAL': 0.05
        }
        df['theme_factor'] = df['theme_id'].map(theme_factors).fillna(0)
        
        # 4. Language-based trust (some languages have more reliable sources in the dataset)
        language_factors = {
            'English': 0.05,
            'French': 0.05,
            'German': 0.05,
            'Japanese': 0.05
        }
        df['language_factor'] = df['language'].map(language_factors).fillna(0)
        
        # 5. Title length factor (very short titles might be less informative)
        df['title_length'] = df['title'].fillna('').apply(len)
        df['title_factor'] = np.clip((df['title_length'] - 20) / 100, -0.05, 0.05)
        
        # 6. Cross-reference factor (if we have entity data)
        if 'entity_count' in df.columns:
            df['entity_factor'] = np.clip(df['entity_count'] / 10, 0, 0.1)
        else:
            df['entity_factor'] = 0
        
        # Calculate final trust score
        df['trust_score'] = 0.5 + df['domain_trust'] * 0.3 + df['country_factor'] + df['theme_factor'] + df['language_factor'] + df['title_factor'] + df['entity_factor']
        
        # Clip to valid range
        df['trust_score'] = np.clip(df['trust_score'], 0.1, 0.9)
        
        logger.info(f"Calculated trust scores for {len(df)} articles")
        return df
    
    def score_entities(self, entities_df, entity_stats_df=None):
        """
        Calculate trust scores for entities
        
        Args:
            entities_df: DataFrame containing entity mentions
            entity_stats_df: DataFrame containing entity statistics (optional)
            
        Returns:
            DataFrame with added trust scores
        """
        logger.info("Calculating trust scores for entities")
        
        # If entity_stats_df is not provided, calculate it
        if entity_stats_df is None:
            entity_stats_df = self._calculate_entity_stats(entities_df)
        
        # Make a copy of the DataFrame
        df = entity_stats_df.copy()
        
        # Initialize trust scores
        df['trust_score'] = 0.5
        
        # 1. Source diversity factor
        if 'source_diversity' in df.columns:
            df['diversity_factor'] = df['source_diversity'] * 0.2
        else:
            df['diversity_factor'] = 0
        
        # 2. Mention count factor
        if 'count' in df.columns:
            max_count = df['count'].max()
            if max_count > 0:
                df['count_factor'] = np.clip(df['count'] / max_count * 0.2, 0, 0.2)
            else:
                df['count_factor'] = 0
        else:
            df['count_factor'] = 0
        
        # 3. Entity type factor (some entity types are more reliable)
        type_factors = {
            'PERSON': 0.05,
            'ORG': 0.05,
            'GPE': 0.05,
            'LOC': 0.05,
            'FACILITY': 0.05,
            'PRODUCT': 0.05,
            'EVENT': 0.05,
            'DATE': 0.1,
            'TIME': 0.1,
            'MONEY': 0.1,
            'PERCENT': 0.1,
            'QUANTITY': 0.1
        }
        df['type_factor'] = df['type'].map(type_factors).fillna(0)
        
        # 4. Source trust factor (if we have article data)
        if 'avg_source_trust' in df.columns:
            df['source_factor'] = (df['avg_source_trust'] - 0.5) * 0.2
        else:
            df['source_factor'] = 0
        
        # Calculate final trust score
        df['trust_score'] = 0.5 + df['diversity_factor'] + df['count_factor'] + df['type_factor'] + df['source_factor']
        
        # Clip to valid range
        df['trust_score'] = np.clip(df['trust_score'], 0.1, 0.9)
        
        logger.info(f"Calculated trust scores for {len(df)} entities")
        return df
    
    def _calculate_entity_stats(self, entities_df):
        """
        Calculate statistics for entities from mentions
        
        Args:
            entities_df: DataFrame containing entity mentions
            
        Returns:
            DataFrame with entity statistics
        """
        logger.info("Calculating entity statistics")
        
        # Group by entity text and type
        entity_counts = entities_df.groupby(['text', 'type']).size().reset_index(name='count')
        
        # Calculate source diversity
        entity_sources = defaultdict(set)
        for _, row in entities_df.iterrows():
            entity_key = (row['text'], row['type'])
            entity_sources[entity_key].add(row.get('article_domain', ''))
        
        # Add source diversity to entity_counts
        entity_counts['num_sources'] = entity_counts.apply(
            lambda row: len(entity_sources.get((row['text'], row['type']), set())),
            axis=1
        )
        
        entity_counts['source_diversity'] = entity_counts.apply(
            lambda row: row['num_sources'] / max(1, row['count']),
            axis=1
        )
        
        logger.info(f"Calculated statistics for {len(entity_counts)} entities")
        return entity_counts
    
    def calculate_cross_reference_scores(self, articles_df, entities_df):
        """
        Calculate cross-reference scores for articles based on entity mentions
        
        Args:
            articles_df: DataFrame containing articles
            entities_df: DataFrame containing entity mentions
            
        Returns:
            Series with cross-reference scores for articles
        """
        logger.info("Calculating cross-reference scores")
        
        # Count entities per article
        article_entity_counts = entities_df.groupby('article_id').size()
        
        # Calculate average entity count
        avg_entity_count = article_entity_counts.mean()
        
        # Calculate cross-reference score
        cross_ref_scores = article_entity_counts / (avg_entity_count * 2)
        
        # Clip to reasonable range
        cross_ref_scores = np.clip(cross_ref_scores, 0, 0.2)
        
        logger.info(f"Calculated cross-reference scores for {len(cross_ref_scores)} articles")
        return cross_ref_scores
    
    def update_domain_trust_scores(self, articles_df):
        """
        Update domain trust scores based on article data
        
        Args:
            articles_df: DataFrame containing articles
            
        Returns:
            Dictionary with updated domain trust scores
        """
        logger.info("Updating domain trust scores")
        
        # Group by domain
        domain_groups = articles_df.groupby('domain')
        
        # Calculate domain statistics
        domain_stats = {}
        for domain, group in domain_groups:
            # Count articles
            article_count = len(group)
            
            # Calculate average trust score (if available)
            if 'trust_score' in group.columns:
                avg_trust = group['trust_score'].mean()
            else:
                avg_trust = 0.5
            
            # Count countries
            countries = group['sourcecountry'].unique()
            country_count = len(countries)
            
            # Count themes
            themes = group['theme_id'].unique()
            theme_count = len(themes)
            
            domain_stats[domain] = {
                'article_count': article_count,
                'avg_trust': avg_trust,
                'country_count': country_count,
                'theme_count': theme_count
            }
        
        # Calculate trust scores
        for domain, stats in domain_stats.items():
            # Base score
            base_score = 0.5
            
            # Adjust for article count (more articles = more established source)
            article_factor = min(0.1, stats['article_count'] / 100)
            
            # Adjust for theme diversity (more themes = more general source)
            theme_factor = min(0.1, stats['theme_count'] / 10)
            
            # Calculate final score
            trust_score = base_score + article_factor + theme_factor
            
            # Clip to valid range
            trust_score = max(0.1, min(0.9, trust_score))
            
            # Update domain trust score
            self.domain_trust_scores[domain] = trust_score
        
        logger.info(f"Updated trust scores for {len(domain_stats)} domains")
        return self.domain_trust_scores
