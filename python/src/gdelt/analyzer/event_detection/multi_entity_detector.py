#!/usr/bin/env python3
"""
GDELT Multi-Entity Event Detector

This module provides functionality for detecting events involving multiple entities.
"""

import os
import numpy as np
import pandas as pd
import logging
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import networkx as nx

from .base_event_detector import BaseEventDetector
from .correlation_analyzer import CorrelationAnalyzer
from .burst_detector import BurstDetector

# Set up logging
logger = logging.getLogger(__name__)

class MultiEntityEventDetector(BaseEventDetector):
    """Class for detecting events involving multiple entities"""

    def __init__(self, db_manager=None):
        """
        Initialize the multi-entity event detector

        Args:
            db_manager: Database manager for accessing stored data
        """
        super().__init__(db_manager)
        
        # Initialize analyzers
        self.correlation_analyzer = CorrelationAnalyzer()
        self.burst_detector = BurstDetector()

    def detect_correlated_events(self, entity_list, start_date=None, end_date=None, 
                               min_correlation=0.7, output_dir=None):
        """
        Detect events where multiple entities are correlated

        Args:
            entity_list: List of entity texts
            start_date: Start date for analysis (None for all data)
            end_date: End date for analysis (None for all data)
            min_correlation: Minimum correlation coefficient to consider
            output_dir: Directory to save results and visualizations

        Returns:
            Dictionary with correlated event detection results
        """
        logger.info(f"Detecting correlated events for {len(entity_list)} entities")
        
        # Get time series data for all entities
        entity_time_series = self.get_multiple_entity_time_series(
            entity_list, 
            start_date, 
            end_date
        )
        
        if not entity_time_series:
            logger.warning("No data available for any entity")
            return None
            
        # Set minimum correlation
        self.correlation_analyzer.min_correlation = min_correlation
        
        # Calculate entity correlations
        correlation_results = self.correlation_analyzer.calculate_entity_correlations(entity_time_series)
        
        # Create correlation network
        correlation_network = self.correlation_analyzer.create_correlation_network(entity_time_series)
        
        # Find entity communities
        communities = self.correlation_analyzer.find_entity_communities(entity_time_series)
        
        # Initialize results
        results = {
            'entities': list(entity_time_series.keys()),
            'start_date': start_date,
            'end_date': end_date,
            'min_correlation': min_correlation,
            'correlation_matrix': correlation_results['correlations'].to_dict(),
            'communities': communities,
            'correlated_pairs': []
        }
        
        # Extract correlated pairs
        for i, entity1 in enumerate(results['entities']):
            for j, entity2 in enumerate(results['entities']):
                if i < j:  # Avoid duplicates
                    corr = correlation_results['correlations'].loc[entity1, entity2]
                    p_value = correlation_results['p_values'].loc[entity1, entity2]
                    
                    if abs(corr) >= min_correlation:
                        results['correlated_pairs'].append({
                            'entity1': entity1,
                            'entity2': entity2,
                            'correlation': float(corr),
                            'p_value': float(p_value)
                        })
        
        # Create visualization if output directory provided
        if output_dir:
            # Create correlation network visualization
            network_path = self._create_correlation_network_visualization(
                correlation_network,
                output_dir
            )
            results['network_visualization'] = network_path
            
            # Save results
            results_path = self.save_event_results(
                results,
                output_dir,
                "correlated_events.json"
            )
            results['results_path'] = results_path
            
        return results

    def detect_co_occurring_events(self, entity_list, start_date=None, end_date=None, 
                                 max_days_gap=3, output_dir=None):
        """
        Detect events where multiple entities have bursts at the same time

        Args:
            entity_list: List of entity texts
            start_date: Start date for analysis (None for all data)
            end_date: End date for analysis (None for all data)
            max_days_gap: Maximum gap between bursts to consider them co-occurring
            output_dir: Directory to save results and visualizations

        Returns:
            Dictionary with co-occurring event detection results
        """
        logger.info(f"Detecting co-occurring events for {len(entity_list)} entities")
        
        # Get time series data for all entities
        entity_time_series = self.get_multiple_entity_time_series(
            entity_list, 
            start_date, 
            end_date
        )
        
        if not entity_time_series:
            logger.warning("No data available for any entity")
            return None
            
        # Set maximum burst gap
        self.burst_detector.max_burst_gap = max_days_gap
        
        # Detect correlated burst events
        correlated_bursts = self.burst_detector.detect_entity_correlation_bursts(entity_time_series)
        
        # Initialize results
        results = {
            'entities': list(entity_time_series.keys()),
            'start_date': start_date,
            'end_date': end_date,
            'max_days_gap': max_days_gap,
            'co_occurring_events': []
        }
        
        # Process correlated bursts
        for i, burst in enumerate(correlated_bursts):
            event = {
                'id': i + 1,
                'start_date': burst['start_date'],
                'end_date': burst['end_date'],
                'entities': burst['entities'],
                'dates': burst['dates'],
                'duration': len(burst['dates']),
                'description': f"Co-occurring burst involving {len(burst['entities'])} entities"
            }
            
            results['co_occurring_events'].append(event)
            
        # Create visualization if output directory provided
        if output_dir:
            # Create co-occurring events visualization
            events_path = self._create_co_occurring_events_visualization(
                entity_time_series,
                results['co_occurring_events'],
                output_dir
            )
            results['events_visualization'] = events_path
            
            # Save results
            results_path = self.save_event_results(
                results,
                output_dir,
                "co_occurring_events.json"
            )
            results['results_path'] = results_path
            
        return results

    def detect_causal_events(self, entity_list, start_date=None, end_date=None, 
                           max_lag=7, min_correlation=0.5, output_dir=None):
        """
        Detect potential causal relationships between entity events

        Args:
            entity_list: List of entity texts
            start_date: Start date for analysis (None for all data)
            end_date: End date for analysis (None for all data)
            max_lag: Maximum lag to consider (in days)
            min_correlation: Minimum correlation coefficient to consider
            output_dir: Directory to save results and visualizations

        Returns:
            Dictionary with causal event detection results
        """
        logger.info(f"Detecting causal events for {len(entity_list)} entities")
        
        # Get time series data for all entities
        entity_time_series = self.get_multiple_entity_time_series(
            entity_list, 
            start_date, 
            end_date
        )
        
        if not entity_time_series:
            logger.warning("No data available for any entity")
            return None
            
        # Set minimum correlation
        self.correlation_analyzer.min_correlation = min_correlation
        
        # Find causal relationships
        causal_relationships = self.correlation_analyzer.find_causal_relationships(
            entity_time_series,
            max_lag=max_lag
        )
        
        # Create lagged correlation network
        lagged_network = self.correlation_analyzer.create_lagged_correlation_network(
            entity_time_series,
            max_lag=max_lag
        )
        
        # Initialize results
        results = {
            'entities': list(entity_time_series.keys()),
            'start_date': start_date,
            'end_date': end_date,
            'max_lag': max_lag,
            'min_correlation': min_correlation,
            'causal_relationships': causal_relationships
        }
        
        # Create visualization if output directory provided
        if output_dir:
            # Create causal network visualization
            network_path = self._create_causal_network_visualization(
                lagged_network,
                output_dir
            )
            results['network_visualization'] = network_path
            
            # Save results
            results_path = self.save_event_results(
                results,
                output_dir,
                "causal_events.json"
            )
            results['results_path'] = results_path
            
        return results

    def _create_correlation_network_visualization(self, correlation_network, output_dir):
        """
        Create visualization of entity correlation network

        Args:
            correlation_network: NetworkX graph of entity correlations
            output_dir: Directory to save the visualization

        Returns:
            Path to the saved visualization
        """
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Create file path
        file_path = os.path.join(output_dir, "correlation_network.png")
        
        # Create figure
        plt.figure(figsize=(12, 10))
        
        # Get node positions using spring layout
        pos = nx.spring_layout(correlation_network, seed=42)
        
        # Get edge weights
        edge_weights = [abs(correlation_network[u][v]['weight']) * 5 for u, v in correlation_network.edges()]
        
        # Draw network
        nx.draw_networkx_nodes(correlation_network, pos, node_size=500, alpha=0.8)
        nx.draw_networkx_edges(correlation_network, pos, width=edge_weights, alpha=0.5)
        nx.draw_networkx_labels(correlation_network, pos, font_size=10)
        
        # Add edge labels
        edge_labels = {(u, v): f"{correlation_network[u][v]['weight']:.2f}" 
                      for u, v in correlation_network.edges()}
        nx.draw_networkx_edge_labels(correlation_network, pos, edge_labels=edge_labels, font_size=8)
        
        # Set title
        plt.title("Entity Correlation Network", fontsize=16)
        
        # Remove axis
        plt.axis('off')
        
        # Adjust layout
        plt.tight_layout()
        
        # Save figure
        plt.savefig(file_path, dpi=300)
        plt.close()
        
        logger.info(f"Created correlation network visualization at {file_path}")
        
        return file_path

    def _create_co_occurring_events_visualization(self, entity_time_series, co_occurring_events, output_dir):
        """
        Create visualization of co-occurring events

        Args:
            entity_time_series: Dictionary mapping entity names to time series
            co_occurring_events: List of co-occurring events
            output_dir: Directory to save the visualization

        Returns:
            Path to the saved visualization
        """
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Create file path
        file_path = os.path.join(output_dir, "co_occurring_events.png")
        
        # Create figure
        fig, ax = plt.subplots(figsize=(14, 8))
        
        # Plot time series for each entity
        for i, (entity, time_series) in enumerate(entity_time_series.items()):
            # Plot with slight offset for visibility
            offset = i * 0.1
            ax.plot(
                time_series.index, 
                time_series.values + offset, 
                label=entity,
                alpha=0.7
            )
            
        # Plot co-occurring events
        for event in co_occurring_events:
            # Get event dates
            event_dates = event['dates']
            
            # Highlight event period
            min_date = min(event_dates)
            max_date = max(event_dates)
            
            ax.axvspan(
                min_date, 
                max_date, 
                alpha=0.2, 
                color='red'
            )
            
            # Add annotation
            ax.annotate(
                f"Event {event['id']}: {len(event['entities'])} entities",
                xy=(min_date, ax.get_ylim()[1] * 0.9),
                xytext=(10, 10),
                textcoords='offset points',
                bbox=dict(boxstyle='round,pad=0.5', fc='yellow', alpha=0.5)
            )
            
        # Set title and labels
        ax.set_title("Co-occurring Entity Events", fontsize=16)
        ax.set_xlabel("Date", fontsize=12)
        ax.set_ylabel("Mentions (with offset)", fontsize=12)
        
        # Format x-axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
        plt.xticks(rotation=45, ha='right')
        
        # Add grid
        ax.grid(True, linestyle='--', alpha=0.7)
        
        # Add legend
        ax.legend(loc='upper left', bbox_to_anchor=(1, 1))
        
        # Adjust layout
        plt.tight_layout()
        
        # Save figure
        plt.savefig(file_path, dpi=300)
        plt.close()
        
        logger.info(f"Created co-occurring events visualization at {file_path}")
        
        return file_path

    def _create_causal_network_visualization(self, causal_network, output_dir):
        """
        Create visualization of causal network

        Args:
            causal_network: NetworkX directed graph of causal relationships
            output_dir: Directory to save the visualization

        Returns:
            Path to the saved visualization
        """
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Create file path
        file_path = os.path.join(output_dir, "causal_network.png")
        
        # Create figure
        plt.figure(figsize=(12, 10))
        
        # Get node positions using spring layout
        pos = nx.spring_layout(causal_network, seed=42)
        
        # Get edge weights and lags
        edge_weights = [abs(causal_network[u][v]['weight']) * 5 for u, v in causal_network.edges()]
        edge_lags = [causal_network[u][v]['lag'] for u, v in causal_network.edges()]
        
        # Draw network
        nx.draw_networkx_nodes(causal_network, pos, node_size=500, alpha=0.8)
        nx.draw_networkx_edges(
            causal_network, 
            pos, 
            width=edge_weights, 
            alpha=0.5,
            arrowsize=20,
            arrowstyle='->'
        )
        nx.draw_networkx_labels(causal_network, pos, font_size=10)
        
        # Add edge labels
        edge_labels = {(u, v): f"r={causal_network[u][v]['weight']:.2f}\nlag={causal_network[u][v]['lag']}" 
                      for u, v in causal_network.edges()}
        nx.draw_networkx_edge_labels(causal_network, pos, edge_labels=edge_labels, font_size=8)
        
        # Set title
        plt.title("Entity Causal Network", fontsize=16)
        
        # Remove axis
        plt.axis('off')
        
        # Adjust layout
        plt.tight_layout()
        
        # Save figure
        plt.savefig(file_path, dpi=300)
        plt.close()
        
        logger.info(f"Created causal network visualization at {file_path}")
        
        return file_path
