#!/usr/bin/env python3
"""
GDELT Correlation Analysis

This module provides correlation analysis functionality for GDELT news data.
"""

import numpy as np
import pandas as pd
import logging
from scipy.stats import pearsonr, spearmanr
import networkx as nx
from datetime import datetime, timedelta

# Set up logging
logger = logging.getLogger(__name__)

class CorrelationAnalyzer:
    """Class for analyzing correlations between entities in news data"""

    def __init__(self, correlation_method='pearson', min_correlation=0.5, min_data_points=10):
        """
        Initialize the correlation analyzer

        Args:
            correlation_method: Method for calculating correlations ('pearson' or 'spearman')
            min_correlation: Minimum correlation coefficient to consider
            min_data_points: Minimum number of data points required for correlation
        """
        self.correlation_method = correlation_method
        self.min_correlation = min_correlation
        self.min_data_points = min_data_points

    def calculate_correlation(self, series1, series2):
        """
        Calculate correlation between two time series

        Args:
            series1: First time series
            series2: Second time series

        Returns:
            Correlation coefficient and p-value
        """
        # Align series
        df = pd.DataFrame({'series1': series1, 'series2': series2})
        df = df.dropna()
        
        # Check if enough data points
        if len(df) < self.min_data_points:
            return 0, 1.0
            
        # Calculate correlation
        if self.correlation_method == 'pearson':
            corr, p_value = pearsonr(df['series1'], df['series2'])
        elif self.correlation_method == 'spearman':
            corr, p_value = spearmanr(df['series1'], df['series2'])
        else:
            logger.warning(f"Unknown correlation method: {self.correlation_method}")
            corr, p_value = 0, 1.0
            
        return corr, p_value

    def calculate_lagged_correlation(self, series1, series2, max_lag=7):
        """
        Calculate correlation with lags between two time series

        Args:
            series1: First time series
            series2: Second time series
            max_lag: Maximum lag to consider (in days)

        Returns:
            Dictionary with lag, correlation coefficient, and p-value
        """
        results = []
        
        # Calculate correlation for each lag
        for lag in range(-max_lag, max_lag + 1):
            if lag < 0:
                # series1 lags behind series2
                s1 = series1.shift(-lag)
                s2 = series2
                lag_direction = 'series1 lags'
            else:
                # series2 lags behind series1
                s1 = series1
                s2 = series2.shift(lag)
                lag_direction = 'series2 lags'
                
            # Calculate correlation
            corr, p_value = self.calculate_correlation(s1, s2)
            
            results.append({
                'lag': lag,
                'lag_direction': lag_direction,
                'correlation': corr,
                'p_value': p_value
            })
            
        # Convert to DataFrame
        results_df = pd.DataFrame(results)
        
        # Find best lag
        best_lag = results_df.loc[results_df['correlation'].abs().idxmax()]
        
        return {
            'all_lags': results_df,
            'best_lag': best_lag
        }

    def calculate_entity_correlations(self, entity_time_series_dict):
        """
        Calculate correlations between multiple entities

        Args:
            entity_time_series_dict: Dictionary mapping entity names to time series data

        Returns:
            DataFrame with pairwise correlations
        """
        entities = list(entity_time_series_dict.keys())
        n_entities = len(entities)
        
        # Initialize correlation matrix
        correlations = np.zeros((n_entities, n_entities))
        p_values = np.ones((n_entities, n_entities))
        
        # Calculate correlations
        for i in range(n_entities):
            for j in range(i+1, n_entities):
                entity1 = entities[i]
                entity2 = entities[j]
                
                series1 = entity_time_series_dict[entity1]
                series2 = entity_time_series_dict[entity2]
                
                corr, p_value = self.calculate_correlation(series1, series2)
                
                correlations[i, j] = corr
                correlations[j, i] = corr
                p_values[i, j] = p_value
                p_values[j, i] = p_value
                
        # Set diagonal to 1
        np.fill_diagonal(correlations, 1.0)
        np.fill_diagonal(p_values, 0.0)
        
        # Create DataFrames
        corr_df = pd.DataFrame(correlations, index=entities, columns=entities)
        p_value_df = pd.DataFrame(p_values, index=entities, columns=entities)
        
        return {
            'correlations': corr_df,
            'p_values': p_value_df
        }

    def calculate_entity_lagged_correlations(self, entity_time_series_dict, max_lag=7):
        """
        Calculate lagged correlations between multiple entities

        Args:
            entity_time_series_dict: Dictionary mapping entity names to time series data
            max_lag: Maximum lag to consider (in days)

        Returns:
            Dictionary with best lag correlations
        """
        entities = list(entity_time_series_dict.keys())
        n_entities = len(entities)
        
        # Initialize result dictionaries
        best_lags = {}
        best_correlations = np.zeros((n_entities, n_entities))
        
        # Calculate lagged correlations
        for i in range(n_entities):
            for j in range(i+1, n_entities):
                entity1 = entities[i]
                entity2 = entities[j]
                
                series1 = entity_time_series_dict[entity1]
                series2 = entity_time_series_dict[entity2]
                
                # Calculate lagged correlation
                lagged_corr = self.calculate_lagged_correlation(series1, series2, max_lag)
                
                # Store best lag
                best_lags[(entity1, entity2)] = {
                    'lag': lagged_corr['best_lag']['lag'],
                    'lag_direction': lagged_corr['best_lag']['lag_direction'],
                    'correlation': lagged_corr['best_lag']['correlation'],
                    'p_value': lagged_corr['best_lag']['p_value']
                }
                
                best_lags[(entity2, entity1)] = {
                    'lag': -lagged_corr['best_lag']['lag'],
                    'lag_direction': 'opposite',
                    'correlation': lagged_corr['best_lag']['correlation'],
                    'p_value': lagged_corr['best_lag']['p_value']
                }
                
                # Store best correlation
                best_correlations[i, j] = lagged_corr['best_lag']['correlation']
                best_correlations[j, i] = lagged_corr['best_lag']['correlation']
                
        # Set diagonal to 1
        np.fill_diagonal(best_correlations, 1.0)
        
        # Create DataFrame
        best_corr_df = pd.DataFrame(best_correlations, index=entities, columns=entities)
        
        return {
            'best_lags': best_lags,
            'best_correlations': best_corr_df
        }

    def create_correlation_network(self, entity_time_series_dict, significant_only=True, p_threshold=0.05):
        """
        Create a network of correlated entities

        Args:
            entity_time_series_dict: Dictionary mapping entity names to time series data
            significant_only: Whether to include only significant correlations
            p_threshold: P-value threshold for significance

        Returns:
            NetworkX graph of entity correlations
        """
        # Calculate correlations
        corr_results = self.calculate_entity_correlations(entity_time_series_dict)
        corr_df = corr_results['correlations']
        p_value_df = corr_results['p_values']
        
        # Create graph
        G = nx.Graph()
        
        # Add nodes
        for entity in corr_df.index:
            G.add_node(entity)
            
        # Add edges
        for i, entity1 in enumerate(corr_df.index):
            for j, entity2 in enumerate(corr_df.columns):
                if i < j:  # Avoid duplicates
                    corr = corr_df.loc[entity1, entity2]
                    p_value = p_value_df.loc[entity1, entity2]
                    
                    # Check if correlation is significant
                    if abs(corr) >= self.min_correlation:
                        if not significant_only or p_value <= p_threshold:
                            G.add_edge(entity1, entity2, weight=corr, p_value=p_value)
        
        return G

    def create_lagged_correlation_network(self, entity_time_series_dict, max_lag=7, significant_only=True, p_threshold=0.05):
        """
        Create a network of entities with lagged correlations

        Args:
            entity_time_series_dict: Dictionary mapping entity names to time series data
            max_lag: Maximum lag to consider (in days)
            significant_only: Whether to include only significant correlations
            p_threshold: P-value threshold for significance

        Returns:
            NetworkX directed graph of entity lagged correlations
        """
        # Calculate lagged correlations
        lagged_results = self.calculate_entity_lagged_correlations(entity_time_series_dict, max_lag)
        best_lags = lagged_results['best_lags']
        
        # Create directed graph
        G = nx.DiGraph()
        
        # Add nodes
        for entity in entity_time_series_dict.keys():
            G.add_node(entity)
            
        # Add edges
        for (entity1, entity2), lag_info in best_lags.items():
            if entity1 != entity2:  # Avoid self-loops
                corr = lag_info['correlation']
                p_value = lag_info['p_value']
                lag = lag_info['lag']
                
                # Check if correlation is significant
                if abs(corr) >= self.min_correlation:
                    if not significant_only or p_value <= p_threshold:
                        # Add edge from leading to lagging entity
                        if lag > 0:
                            # entity1 leads entity2
                            G.add_edge(entity1, entity2, weight=corr, p_value=p_value, lag=lag)
                        elif lag < 0:
                            # entity2 leads entity1
                            G.add_edge(entity2, entity1, weight=corr, p_value=p_value, lag=-lag)
        
        return G

    def find_entity_communities(self, entity_time_series_dict):
        """
        Find communities of correlated entities

        Args:
            entity_time_series_dict: Dictionary mapping entity names to time series data

        Returns:
            List of entity communities
        """
        # Create correlation network
        G = self.create_correlation_network(entity_time_series_dict)
        
        # Find communities
        communities = list(nx.algorithms.community.greedy_modularity_communities(G))
        
        # Convert to list of entity names
        entity_communities = []
        for community in communities:
            entity_communities.append(list(community))
            
        return entity_communities

    def find_causal_relationships(self, entity_time_series_dict, max_lag=7, p_threshold=0.05):
        """
        Find potential causal relationships between entities

        Args:
            entity_time_series_dict: Dictionary mapping entity names to time series data
            max_lag: Maximum lag to consider (in days)
            p_threshold: P-value threshold for significance

        Returns:
            List of potential causal relationships
        """
        # Create lagged correlation network
        G = self.create_lagged_correlation_network(
            entity_time_series_dict, 
            max_lag=max_lag,
            significant_only=True,
            p_threshold=p_threshold
        )
        
        # Find potential causal relationships
        causal_relationships = []
        
        for u, v, data in G.edges(data=True):
            causal_relationships.append({
                'cause': u,
                'effect': v,
                'lag': data['lag'],
                'correlation': data['weight'],
                'p_value': data['p_value']
            })
            
        # Sort by correlation strength
        causal_relationships.sort(key=lambda x: abs(x['correlation']), reverse=True)
        
        return causal_relationships
