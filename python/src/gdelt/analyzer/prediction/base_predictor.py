#!/usr/bin/env python3
"""
GDELT Base Predictive Event Detector

This module provides the base class for predicting future events based on patterns in news coverage.
"""

import os
import pandas as pd
import numpy as np
import logging
import json
from datetime import datetime, timedelta
from collections import defaultdict

# Set up logging
logger = logging.getLogger(__name__)

class BasePredictor:
    """Base class for predicting future events based on patterns in news coverage"""

    def __init__(self, db_manager=None):
        """
        Initialize the base predictor

        Args:
            db_manager: DatabaseManager instance for accessing stored data
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

    def prepare_time_series(self, articles_df):
        """
        Prepare a time series from articles dataframe

        Args:
            articles_df: DataFrame of articles

        Returns:
            Pandas Series with daily counts
        """
        # Convert seendate to datetime
        articles_df['seendate'] = pd.to_datetime(articles_df['seendate'])

        # Group articles by date
        articles_df['date'] = articles_df['seendate'].dt.date
        daily_counts = articles_df.groupby('date').size()

        # Create time series
        time_series = pd.Series(daily_counts)

        # Ensure the time series has a continuous date range
        date_range = pd.date_range(
            start=time_series.index.min(),
            end=time_series.index.max()
        )
        time_series = time_series.reindex(date_range, fill_value=0)

        return time_series

    def create_prediction_results(self, entity_text, time_series, predictions, 
                                ensemble_predictions, prediction_chart_path, days_to_predict):
        """
        Create prediction results dictionary

        Args:
            entity_text: Text of the entity
            time_series: Time series of historical data
            predictions: Dictionary of predictions from different models
            ensemble_predictions: Dictionary of ensemble predictions
            prediction_chart_path: Path to the prediction chart
            days_to_predict: Number of days predicted

        Returns:
            Dictionary with prediction results
        """
        # Create prediction results
        prediction_results = {
            'entity': entity_text,
            'historical_start_date': time_series.index[0].strftime('%Y-%m-%d'),
            'historical_end_date': time_series.index[-1].strftime('%Y-%m-%d'),
            'prediction_start_date': (time_series.index[-1] + timedelta(days=1)).strftime('%Y-%m-%d'),
            'prediction_end_date': (time_series.index[-1] + timedelta(days=days_to_predict)).strftime('%Y-%m-%d'),
            'historical_data': {str(k): int(v) for k, v in time_series.to_dict().items()},
            'predictions': {
                'arima': {str(k): float(v) for k, v in predictions.get('arima', {}).items()},
                'exponential_smoothing': {str(k): float(v) for k, v in predictions.get('exponential_smoothing', {}).items()},
                'linear_regression': {str(k): float(v) for k, v in predictions.get('linear_regression', {}).items()},
                'ensemble': {str(k): float(v) for k, v in ensemble_predictions.items()}
            },
            'prediction_chart': prediction_chart_path
        }

        return prediction_results

    def save_prediction_results(self, prediction_results, output_dir):
        """
        Save prediction results to a JSON file

        Args:
            prediction_results: Dictionary with prediction results
            output_dir: Directory to save the results

        Returns:
            Path to the saved file
        """
        entity = prediction_results['entity']
        
        # Save prediction results
        prediction_json_path = os.path.join(
            output_dir,
            f"{entity.replace(' ', '_')}_prediction.json"
        )
        with open(prediction_json_path, 'w') as f:
            json.dump(prediction_results, f, indent=2)

        logger.info(f"Saved prediction results to {prediction_json_path}")

        return prediction_json_path
