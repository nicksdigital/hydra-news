#!/usr/bin/env python3
"""
GDELT Burst Detection

This module provides burst detection functionality for GDELT news data.
"""

import numpy as np
import pandas as pd
import logging
from datetime import datetime, timedelta
from scipy.signal import find_peaks

# Set up logging
logger = logging.getLogger(__name__)

class BurstDetector:
    """Class for detecting bursts in time series data"""

    def __init__(self, sensitivity=2.0, window_size=3, min_burst_duration=1, max_burst_gap=1):
        """
        Initialize the burst detector

        Args:
            sensitivity: Sensitivity threshold for burst detection
            window_size: Size of the sliding window for baseline calculation
            min_burst_duration: Minimum duration of a burst (in days)
            max_burst_gap: Maximum gap between consecutive burst days to be considered the same burst
        """
        self.sensitivity = sensitivity
        self.window_size = window_size
        self.min_burst_duration = min_burst_duration
        self.max_burst_gap = max_burst_gap

    def detect_bursts(self, time_series):
        """
        Detect bursts in time series data

        Args:
            time_series: Time series data

        Returns:
            DataFrame with burst scores and labels
        """
        # Convert to DataFrame if Series
        if isinstance(time_series, pd.Series):
            df = pd.DataFrame(time_series)
            df.columns = ['value']
        else:
            df = time_series.copy()
            
        # Create result DataFrame
        result = pd.DataFrame(index=df.index)
        result['value'] = df['value']
        
        # Initialize burst scores
        result['burst_score'] = 0.0
        result['is_burst'] = False
        
        # Calculate burst patterns
        if len(df) > self.window_size:
            # Calculate rolling statistics
            rolling_mean = df['value'].rolling(window=self.window_size, min_periods=1).mean()
            rolling_std = df['value'].rolling(window=self.window_size, min_periods=1).std()
            
            # Calculate burst scores
            result['burst_score'] = (df['value'] - rolling_mean) / (rolling_std + 1e-10)
            
            # Determine if burst
            result['is_burst'] = result['burst_score'] > self.sensitivity
            
            # Ensure bursts are increases, not decreases
            result.loc[df['value'] < rolling_mean, 'is_burst'] = False
        
        return result

    def detect_burst_events(self, time_series):
        """
        Detect burst events (consecutive burst days)

        Args:
            time_series: Time series data

        Returns:
            List of burst events
        """
        # Detect bursts
        bursts = self.detect_bursts(time_series)
        
        # Find burst events
        burst_events = []
        current_burst = None
        
        for i, (date, row) in enumerate(bursts.iterrows()):
            if row['is_burst']:
                if current_burst is None:
                    # Start new burst
                    current_burst = {
                        'start_date': date,
                        'end_date': date,
                        'peak_date': date,
                        'peak_value': row['value'],
                        'peak_score': row['burst_score'],
                        'duration': 1,
                        'values': [row['value']],
                        'dates': [date]
                    }
                else:
                    # Check if this is part of the current burst
                    if isinstance(date, pd.Timestamp) and isinstance(current_burst['end_date'], pd.Timestamp):
                        days_gap = (date - current_burst['end_date']).days
                    else:
                        days_gap = i - bursts.index.get_loc(current_burst['end_date'])
                        
                    if days_gap <= self.max_burst_gap:
                        # Extend current burst
                        current_burst['end_date'] = date
                        current_burst['duration'] += 1
                        current_burst['values'].append(row['value'])
                        current_burst['dates'].append(date)
                        
                        # Update peak if needed
                        if row['value'] > current_burst['peak_value']:
                            current_burst['peak_date'] = date
                            current_burst['peak_value'] = row['value']
                            current_burst['peak_score'] = row['burst_score']
                    else:
                        # End current burst and start new one
                        if current_burst['duration'] >= self.min_burst_duration:
                            burst_events.append(current_burst)
                            
                        current_burst = {
                            'start_date': date,
                            'end_date': date,
                            'peak_date': date,
                            'peak_value': row['value'],
                            'peak_score': row['burst_score'],
                            'duration': 1,
                            'values': [row['value']],
                            'dates': [date]
                        }
            else:
                # End current burst if exists
                if current_burst is not None:
                    if current_burst['duration'] >= self.min_burst_duration:
                        burst_events.append(current_burst)
                    current_burst = None
        
        # Add last burst if exists
        if current_burst is not None and current_burst['duration'] >= self.min_burst_duration:
            burst_events.append(current_burst)
            
        return burst_events

    def detect_peaks(self, time_series, prominence=1.0, width=1):
        """
        Detect peaks in time series data

        Args:
            time_series: Time series data
            prominence: Required prominence of peaks
            width: Required width of peaks

        Returns:
            DataFrame with peak information
        """
        # Convert to DataFrame if Series
        if isinstance(time_series, pd.Series):
            values = time_series.values
            index = time_series.index
        else:
            values = time_series['value'].values
            index = time_series.index
            
        # Find peaks
        peaks, properties = find_peaks(values, prominence=prominence, width=width)
        
        # Create result DataFrame
        if len(peaks) > 0:
            result = pd.DataFrame({
                'date': [index[i] for i in peaks],
                'value': [values[i] for i in peaks],
                'prominence': properties['prominences'],
                'width': properties['widths']
            })
            
            # Sort by prominence
            result = result.sort_values('prominence', ascending=False)
        else:
            result = pd.DataFrame(columns=['date', 'value', 'prominence', 'width'])
            
        return result

    def detect_multi_scale_bursts(self, time_series, scales=[3, 7, 14, 30]):
        """
        Detect bursts at multiple time scales

        Args:
            time_series: Time series data
            scales: List of time scales (window sizes) to use

        Returns:
            DataFrame with multi-scale burst scores and labels
        """
        # Convert to DataFrame if Series
        if isinstance(time_series, pd.Series):
            df = pd.DataFrame(time_series)
            df.columns = ['value']
        else:
            df = time_series.copy()
            
        # Create result DataFrame
        result = pd.DataFrame(index=df.index)
        result['value'] = df['value']
        
        # Detect bursts at each scale
        for scale in scales:
            # Save original window size
            original_window_size = self.window_size
            
            # Set window size for this scale
            self.window_size = scale
            
            # Detect bursts
            bursts = self.detect_bursts(time_series)
            
            # Add to result
            result[f'burst_score_{scale}'] = bursts['burst_score']
            result[f'is_burst_{scale}'] = bursts['is_burst']
            
            # Restore original window size
            self.window_size = original_window_size
            
        # Calculate combined score
        score_columns = [f'burst_score_{scale}' for scale in scales]
        result['combined_burst_score'] = result[score_columns].mean(axis=1)
        
        # Determine if combined burst
        burst_columns = [f'is_burst_{scale}' for scale in scales]
        result['is_combined_burst'] = result[burst_columns].any(axis=1)
        
        return result

    def detect_entity_correlation_bursts(self, entity_time_series_dict):
        """
        Detect correlated bursts across multiple entities

        Args:
            entity_time_series_dict: Dictionary mapping entity names to time series data

        Returns:
            Dictionary with correlated burst events
        """
        # Detect bursts for each entity
        entity_bursts = {}
        for entity, time_series in entity_time_series_dict.items():
            entity_bursts[entity] = self.detect_burst_events(time_series)
            
        # Find correlated burst events
        correlated_events = []
        
        # Get all unique dates
        all_dates = set()
        for entity, bursts in entity_bursts.items():
            for burst in bursts:
                all_dates.update(burst['dates'])
                
        # Count entities with bursts on each date
        date_counts = {}
        date_entities = {}
        for date in all_dates:
            date_entities[date] = []
            for entity, bursts in entity_bursts.items():
                for burst in bursts:
                    if date in burst['dates']:
                        date_entities[date].append(entity)
                        break
                        
            date_counts[date] = len(date_entities[date])
            
        # Find dates with multiple entities having bursts
        correlated_dates = {date: entities for date, entities in date_entities.items() if len(entities) > 1}
        
        # Group consecutive correlated dates
        if correlated_dates:
            sorted_dates = sorted(correlated_dates.keys())
            current_event = {
                'start_date': sorted_dates[0],
                'end_date': sorted_dates[0],
                'entities': correlated_dates[sorted_dates[0]],
                'dates': [sorted_dates[0]]
            }
            
            for i in range(1, len(sorted_dates)):
                date = sorted_dates[i]
                prev_date = sorted_dates[i-1]
                
                # Check if consecutive
                if isinstance(date, pd.Timestamp) and isinstance(prev_date, pd.Timestamp):
                    days_gap = (date - prev_date).days
                else:
                    days_gap = 2  # Non-consecutive by default
                    
                if days_gap <= self.max_burst_gap:
                    # Extend current event
                    current_event['end_date'] = date
                    current_event['entities'] = list(set(current_event['entities'] + correlated_dates[date]))
                    current_event['dates'].append(date)
                else:
                    # End current event and start new one
                    correlated_events.append(current_event)
                    current_event = {
                        'start_date': date,
                        'end_date': date,
                        'entities': correlated_dates[date],
                        'dates': [date]
                    }
                    
            # Add last event
            correlated_events.append(current_event)
            
        return correlated_events
