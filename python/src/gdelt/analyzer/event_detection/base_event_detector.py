#!/usr/bin/env python3
"""
GDELT Base Event Detector

This module provides the base class for event detection in GDELT news data.
"""

import os
import numpy as np
import pandas as pd
import logging
from datetime import datetime, timedelta
import json

# Set up logging
logger = logging.getLogger(__name__)

class BaseEventDetector:
    """Base class for event detection in news data"""

    def __init__(self, db_manager=None):
        """
        Initialize the base event detector

        Args:
            db_manager: Database manager for accessing stored data
        """
        self.db_manager = db_manager

    def get_entity_articles(self, entity_text, start_date=None, end_date=None):
        """
        Get articles mentioning an entity from the database

        Args:
            entity_text: Text of the entity to get articles for
            start_date: Start date for filtering articles (None for all data)
            end_date: End date for filtering articles (None for all data)

        Returns:
            DataFrame of articles
        """
        if not self.db_manager or not self.db_manager.conn:
            logger.warning("No database connection available")
            return pd.DataFrame()

        # Get entity ID
        self.db_manager.cursor.execute(
            "SELECT id FROM entities WHERE text = ?",
            (entity_text,)
        )
        result = self.db_manager.cursor.fetchone()

        if not result:
            logger.warning(f"Entity '{entity_text}' not found in database")
            return pd.DataFrame()

        entity_id = result[0]

        # Get articles mentioning the entity
        query = """
        SELECT a.id, a.url, a.title, a.seendate, a.language, a.domain,
               a.sourcecountry, a.theme_id, a.theme_description, a.trust_score
        FROM articles a
        JOIN article_entities ae ON a.id = ae.article_id
        WHERE ae.entity_id = ?
        """

        params = [entity_id]

        # Add date filters if provided
        if start_date:
            query += " AND a.seendate >= ?"
            params.append(start_date)

        if end_date:
            query += " AND a.seendate <= ?"
            params.append(end_date)

        # Order by date
        query += " ORDER BY a.seendate"

        articles_df = pd.read_sql_query(query, self.db_manager.conn, params=params)

        if articles_df.empty:
            logger.warning(f"No articles found for entity '{entity_text}'")
            return pd.DataFrame()

        logger.info(f"Found {len(articles_df)} articles for entity '{entity_text}'")
        return articles_df

    def prepare_time_series(self, articles_df, freq='D'):
        """
        Prepare a time series from articles dataframe

        Args:
            articles_df: DataFrame of articles
            freq: Frequency for resampling ('D' for daily, 'W' for weekly, etc.)

        Returns:
            Pandas Series with counts at the specified frequency
        """
        # Convert seendate to datetime
        articles_df['seendate'] = pd.to_datetime(articles_df['seendate'])

        # Set seendate as index
        df = articles_df.set_index('seendate')

        # Resample to get counts
        time_series = df.resample(freq).size()

        # Fill missing values with 0
        time_series = time_series.fillna(0)

        return time_series

    def get_entity_time_series(self, entity_text, start_date=None, end_date=None, freq='D'):
        """
        Get time series data for an entity

        Args:
            entity_text: Text of the entity
            start_date: Start date for filtering articles (None for all data)
            end_date: End date for filtering articles (None for all data)
            freq: Frequency for resampling ('D' for daily, 'W' for weekly, etc.)

        Returns:
            Pandas Series with entity mentions over time
        """
        # Get articles for the entity
        articles_df = self.get_entity_articles(entity_text, start_date, end_date)
        
        if articles_df.empty:
            return pd.Series()
            
        # Prepare time series
        time_series = self.prepare_time_series(articles_df, freq)
        
        return time_series

    def get_multiple_entity_time_series(self, entity_list, start_date=None, end_date=None, freq='D'):
        """
        Get time series data for multiple entities

        Args:
            entity_list: List of entity texts
            start_date: Start date for filtering articles (None for all data)
            end_date: End date for filtering articles (None for all data)
            freq: Frequency for resampling ('D' for daily, 'W' for weekly, etc.)

        Returns:
            Dictionary mapping entity names to time series
        """
        entity_time_series = {}
        
        for entity in entity_list:
            time_series = self.get_entity_time_series(entity, start_date, end_date, freq)
            
            if not time_series.empty:
                entity_time_series[entity] = time_series
                
        return entity_time_series

    def save_event_results(self, event_results, output_dir, filename):
        """
        Save event detection results to a JSON file

        Args:
            event_results: Dictionary with event detection results
            output_dir: Directory to save the results
            filename: Name of the output file

        Returns:
            Path to the saved file
        """
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Create file path
        file_path = os.path.join(output_dir, filename)
        
        # Convert dates to strings
        results_copy = self._convert_dates_to_strings(event_results)
        
        # Save to JSON
        with open(file_path, 'w') as f:
            json.dump(results_copy, f, indent=2)
            
        logger.info(f"Saved event results to {file_path}")
        
        return file_path

    def _convert_dates_to_strings(self, obj):
        """
        Convert datetime objects to strings in a nested structure

        Args:
            obj: Object to convert (dict, list, datetime, etc.)

        Returns:
            Object with datetime objects converted to strings
        """
        if isinstance(obj, dict):
            return {k: self._convert_dates_to_strings(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_dates_to_strings(item) for item in obj]
        elif isinstance(obj, (datetime, pd.Timestamp)):
            return obj.strftime('%Y-%m-%d')
        elif isinstance(obj, pd.Series):
            if isinstance(obj.index, pd.DatetimeIndex):
                return {date.strftime('%Y-%m-%d'): value for date, value in obj.items()}
            else:
                return obj.to_dict()
        elif isinstance(obj, pd.DataFrame):
            if isinstance(obj.index, pd.DatetimeIndex):
                obj = obj.reset_index()
            return obj.to_dict(orient='records')
        else:
            return obj
