#!/usr/bin/env python3
"""
GDELT Entity Event Detector

This module provides functionality for detecting events related to specific entities.
"""

import os
import numpy as np
import pandas as pd
import logging
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from .base_event_detector import BaseEventDetector
from .anomaly_detector import AnomalyDetector
from .burst_detector import BurstDetector

# Set up logging
logger = logging.getLogger(__name__)

class EntityEventDetector(BaseEventDetector):
    """Class for detecting events related to specific entities"""

    def __init__(self, db_manager=None):
        """
        Initialize the entity event detector

        Args:
            db_manager: Database manager for accessing stored data
        """
        super().__init__(db_manager)
        
        # Initialize detectors
        self.anomaly_detector = AnomalyDetector(method='isolation_forest')
        self.burst_detector = BurstDetector(sensitivity=2.0)

    def detect_entity_events(self, entity_text, start_date=None, end_date=None, 
                           detection_methods=None, output_dir=None):
        """
        Detect events for a specific entity

        Args:
            entity_text: Text of the entity
            start_date: Start date for analysis (None for all data)
            end_date: End date for analysis (None for all data)
            detection_methods: List of detection methods to use (None for all)
            output_dir: Directory to save results and visualizations

        Returns:
            Dictionary with event detection results
        """
        logger.info(f"Detecting events for entity: {entity_text}")
        
        # Get time series data
        time_series = self.get_entity_time_series(entity_text, start_date, end_date)
        
        if time_series.empty:
            logger.warning(f"No data available for entity: {entity_text}")
            return None
            
        # Set default detection methods if not provided
        if detection_methods is None:
            detection_methods = ['anomaly', 'burst', 'change_point']
            
        # Initialize results
        results = {
            'entity': entity_text,
            'start_date': time_series.index[0],
            'end_date': time_series.index[-1],
            'total_mentions': int(time_series.sum()),
            'avg_daily_mentions': float(time_series.mean()),
            'max_daily_mentions': int(time_series.max()),
            'events': []
        }
        
        # Detect events using different methods
        all_events = []
        
        if 'anomaly' in detection_methods:
            anomaly_events = self._detect_anomaly_events(time_series, entity_text)
            all_events.extend(anomaly_events)
            results['anomaly_events'] = anomaly_events
            
        if 'burst' in detection_methods:
            burst_events = self._detect_burst_events(time_series, entity_text)
            all_events.extend(burst_events)
            results['burst_events'] = burst_events
            
        if 'change_point' in detection_methods:
            change_point_events = self._detect_change_point_events(time_series, entity_text)
            all_events.extend(change_point_events)
            results['change_point_events'] = change_point_events
            
        # Combine and deduplicate events
        combined_events = self._combine_events(all_events)
        results['events'] = combined_events
        
        # Create visualization if output directory provided
        if output_dir:
            # Create visualization
            viz_path = self._create_event_visualization(
                time_series, 
                combined_events, 
                entity_text, 
                output_dir
            )
            results['visualization'] = viz_path
            
            # Save results
            results_path = self.save_event_results(
                results,
                output_dir,
                f"{entity_text.replace(' ', '_')}_events.json"
            )
            results['results_path'] = results_path
            
        return results

    def _detect_anomaly_events(self, time_series, entity_text):
        """
        Detect anomaly events in time series data

        Args:
            time_series: Time series data
            entity_text: Text of the entity

        Returns:
            List of anomaly events
        """
        logger.info(f"Detecting anomaly events for entity: {entity_text}")
        
        # Fit anomaly detector
        self.anomaly_detector.fit(time_series)
        
        # Detect anomalies
        anomalies = self.anomaly_detector.detect_anomalies_with_context(time_series)
        
        if anomalies.empty:
            return []
            
        # Extract anomaly events
        events = []
        
        for date, row in anomalies[anomalies['is_combined_anomaly']].iterrows():
            events.append({
                'date': date,
                'type': 'anomaly',
                'value': float(row['value']),
                'score': float(row['combined_score']),
                'description': f"Anomalous mention count for {entity_text}"
            })
            
        logger.info(f"Detected {len(events)} anomaly events for entity: {entity_text}")
        
        return events

    def _detect_burst_events(self, time_series, entity_text):
        """
        Detect burst events in time series data

        Args:
            time_series: Time series data
            entity_text: Text of the entity

        Returns:
            List of burst events
        """
        logger.info(f"Detecting burst events for entity: {entity_text}")
        
        # Detect burst events
        burst_events = self.burst_detector.detect_burst_events(time_series)
        
        if not burst_events:
            return []
            
        # Convert to standard format
        events = []
        
        for i, burst in enumerate(burst_events):
            events.append({
                'date': burst['peak_date'],
                'type': 'burst',
                'value': float(burst['peak_value']),
                'score': float(burst['peak_score']),
                'duration': burst['duration'],
                'start_date': burst['start_date'],
                'end_date': burst['end_date'],
                'description': f"Burst in mentions for {entity_text} (duration: {burst['duration']} days)"
            })
            
        logger.info(f"Detected {len(events)} burst events for entity: {entity_text}")
        
        return events

    def _detect_change_point_events(self, time_series, entity_text):
        """
        Detect change point events in time series data

        Args:
            time_series: Time series data
            entity_text: Text of the entity

        Returns:
            List of change point events
        """
        logger.info(f"Detecting change point events for entity: {entity_text}")
        
        # Detect change points
        change_points = self.anomaly_detector.detect_change_points(time_series)
        
        if change_points.empty:
            return []
            
        # Extract change point events
        events = []
        
        for date, row in change_points[change_points['is_change_point']].iterrows():
            events.append({
                'date': date,
                'type': 'change_point',
                'value': float(row['value']),
                'score': float(row['change_point_score']),
                'description': f"Change point in mention pattern for {entity_text}"
            })
            
        logger.info(f"Detected {len(events)} change point events for entity: {entity_text}")
        
        return events

    def _combine_events(self, events, max_days_gap=3):
        """
        Combine and deduplicate events

        Args:
            events: List of events
            max_days_gap: Maximum gap between events to consider them the same

        Returns:
            List of combined events
        """
        if not events:
            return []
            
        # Sort events by date
        sorted_events = sorted(events, key=lambda x: x['date'])
        
        # Combine events that are close in time
        combined_events = []
        current_event = sorted_events[0].copy()
        current_event['event_types'] = [current_event['type']]
        
        for event in sorted_events[1:]:
            # Calculate days gap
            if isinstance(event['date'], pd.Timestamp) and isinstance(current_event['date'], pd.Timestamp):
                days_gap = (event['date'] - current_event['date']).days
            else:
                days_gap = abs((event['date'] - current_event['date']).days)
                
            if days_gap <= max_days_gap:
                # Combine events
                if event['score'] > current_event['score']:
                    # Keep the event with the higher score
                    current_event.update({
                        'date': event['date'],
                        'value': event['value'],
                        'score': event['score'],
                        'description': event['description']
                    })
                    
                # Add event type if not already present
                if event['type'] not in current_event['event_types']:
                    current_event['event_types'].append(event['type'])
                    
                # Update description
                current_event['description'] = f"Event detected as: {', '.join(current_event['event_types'])}"
            else:
                # Add current event to results and start a new one
                combined_events.append(current_event)
                current_event = event.copy()
                current_event['event_types'] = [current_event['type']]
                
        # Add the last event
        combined_events.append(current_event)
        
        return combined_events

    def _create_event_visualization(self, time_series, events, entity_text, output_dir):
        """
        Create visualization of entity events

        Args:
            time_series: Time series data
            events: List of detected events
            entity_text: Text of the entity
            output_dir: Directory to save the visualization

        Returns:
            Path to the saved visualization
        """
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Create file path
        file_path = os.path.join(output_dir, f"{entity_text.replace(' ', '_')}_events.png")
        
        # Create figure
        plt.figure(figsize=(12, 6))
        
        # Plot time series
        plt.plot(time_series.index, time_series.values, 'b-', label='Mentions')
        
        # Plot events
        for event in events:
            plt.scatter(
                event['date'], 
                event['value'], 
                c='r', 
                s=100, 
                marker='*', 
                zorder=5
            )
            
            # Add annotation
            plt.annotate(
                f"{', '.join(event['event_types'])}",
                xy=(event['date'], event['value']),
                xytext=(10, 10),
                textcoords='offset points',
                bbox=dict(boxstyle='round,pad=0.5', fc='yellow', alpha=0.5)
            )
            
        # Set title and labels
        plt.title(f"Events for '{entity_text}'", fontsize=14)
        plt.xlabel('Date', fontsize=12)
        plt.ylabel('Mentions', fontsize=12)
        
        # Format x-axis
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        plt.gca().xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
        plt.xticks(rotation=45, ha='right')
        
        # Add grid
        plt.grid(True, linestyle='--', alpha=0.7)
        
        # Add legend
        plt.legend()
        
        # Adjust layout
        plt.tight_layout()
        
        # Save figure
        plt.savefig(file_path, dpi=300)
        plt.close()
        
        logger.info(f"Created event visualization for '{entity_text}' at {file_path}")
        
        return file_path

    def detect_events_for_multiple_entities(self, entity_list, start_date=None, end_date=None, 
                                          detection_methods=None, output_dir=None):
        """
        Detect events for multiple entities

        Args:
            entity_list: List of entity texts
            start_date: Start date for analysis (None for all data)
            end_date: End date for analysis (None for all data)
            detection_methods: List of detection methods to use (None for all)
            output_dir: Directory to save results and visualizations

        Returns:
            Dictionary mapping entity names to event detection results
        """
        logger.info(f"Detecting events for {len(entity_list)} entities")
        
        # Initialize results
        results = {}
        
        # Detect events for each entity
        for entity in entity_list:
            entity_results = self.detect_entity_events(
                entity,
                start_date,
                end_date,
                detection_methods,
                output_dir
            )
            
            if entity_results:
                results[entity] = entity_results
                
        # Save combined results if output directory provided
        if output_dir:
            combined_results = {
                'entities': list(results.keys()),
                'start_date': start_date,
                'end_date': end_date,
                'detection_methods': detection_methods,
                'entity_results': results
            }
            
            combined_path = self.save_event_results(
                combined_results,
                output_dir,
                "combined_entity_events.json"
            )
            
        return results
