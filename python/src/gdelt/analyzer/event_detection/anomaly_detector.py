#!/usr/bin/env python3
"""
GDELT Anomaly Detection

This module provides anomaly detection functionality for GDELT news data.
"""

import numpy as np
import pandas as pd
import logging
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.svm import OneClassSVM
from scipy import stats
from datetime import datetime, timedelta

# Set up logging
logger = logging.getLogger(__name__)

class AnomalyDetector:
    """Class for detecting anomalies in time series data"""

    def __init__(self, method='isolation_forest', contamination=0.05):
        """
        Initialize the anomaly detector

        Args:
            method: Anomaly detection method ('isolation_forest', 'local_outlier_factor', 
                   'one_class_svm', 'z_score', 'iqr', 'moving_average')
            contamination: Expected proportion of outliers in the data
        """
        self.method = method
        self.contamination = contamination
        self.model = None

    def _prepare_features(self, time_series):
        """
        Prepare features for anomaly detection

        Args:
            time_series: Time series data

        Returns:
            Feature matrix
        """
        # Convert to DataFrame if Series
        if isinstance(time_series, pd.Series):
            df = pd.DataFrame(time_series)
            df.columns = ['value']
        else:
            df = time_series.copy()
            
        # Create lag features
        for lag in [1, 2, 3, 7]:
            if len(df) > lag:
                df[f'lag_{lag}'] = df['value'].shift(lag)
                
        # Create rolling statistics
        if len(df) > 7:
            df['rolling_mean_7'] = df['value'].rolling(window=7, min_periods=1).mean()
            df['rolling_std_7'] = df['value'].rolling(window=7, min_periods=1).std()
            
        # Create day of week features
        if isinstance(df.index, pd.DatetimeIndex):
            df['day_of_week'] = df.index.dayofweek
            
        # Drop rows with NaN values
        df = df.dropna()
        
        return df

    def fit(self, time_series):
        """
        Fit the anomaly detection model

        Args:
            time_series: Time series data

        Returns:
            Self
        """
        # Prepare features
        df = self._prepare_features(time_series)
        
        if df.empty:
            logger.warning("Empty feature matrix after preparation")
            return self
            
        # Extract features
        X = df.values
        
        # Fit model based on method
        if self.method == 'isolation_forest':
            self.model = IsolationForest(
                contamination=self.contamination,
                random_state=42
            )
            self.model.fit(X)
        elif self.method == 'local_outlier_factor':
            self.model = LocalOutlierFactor(
                n_neighbors=20,
                contamination=self.contamination
            )
            self.model.fit(X)
        elif self.method == 'one_class_svm':
            self.model = OneClassSVM(
                nu=self.contamination,
                kernel="rbf",
                gamma='scale'
            )
            self.model.fit(X)
        elif self.method in ['z_score', 'iqr', 'moving_average']:
            # These methods don't require fitting
            self.model = None
        else:
            logger.warning(f"Unknown method: {self.method}")
            
        return self

    def detect_anomalies(self, time_series):
        """
        Detect anomalies in time series data

        Args:
            time_series: Time series data

        Returns:
            DataFrame with anomaly scores and labels
        """
        # Prepare features
        df = self._prepare_features(time_series)
        
        if df.empty:
            logger.warning("Empty feature matrix after preparation")
            return pd.DataFrame()
            
        # Create result DataFrame
        result = pd.DataFrame(index=df.index)
        result['value'] = df['value']
        
        # Detect anomalies based on method
        if self.method == 'isolation_forest' and self.model is not None:
            # Predict anomaly scores (-1 for outliers, 1 for inliers)
            result['anomaly_score'] = self.model.decision_function(df.values)
            result['is_anomaly'] = self.model.predict(df.values) == -1
        elif self.method == 'local_outlier_factor' and self.model is not None:
            # Predict anomaly scores (negative values for outliers)
            result['anomaly_score'] = -self.model._decision_function(df.values)
            result['is_anomaly'] = self.model.predict(df.values) == -1
        elif self.method == 'one_class_svm' and self.model is not None:
            # Predict anomaly scores (negative values for outliers)
            result['anomaly_score'] = self.model.decision_function(df.values)
            result['is_anomaly'] = self.model.predict(df.values) == -1
        elif self.method == 'z_score':
            # Calculate Z-scores
            z_scores = np.abs(stats.zscore(df['value']))
            result['anomaly_score'] = z_scores
            result['is_anomaly'] = z_scores > 3.0  # Threshold for Z-score
        elif self.method == 'iqr':
            # Calculate IQR
            Q1 = df['value'].quantile(0.25)
            Q3 = df['value'].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            # Calculate anomaly scores
            result['anomaly_score'] = df['value'].apply(
                lambda x: max(0, (x - upper_bound) / IQR) if x > upper_bound else max(0, (lower_bound - x) / IQR) if x < lower_bound else 0
            )
            result['is_anomaly'] = (df['value'] < lower_bound) | (df['value'] > upper_bound)
        elif self.method == 'moving_average':
            # Calculate moving average
            window_size = min(7, len(df))
            rolling_mean = df['value'].rolling(window=window_size, min_periods=1).mean()
            rolling_std = df['value'].rolling(window=window_size, min_periods=1).std()
            
            # Calculate anomaly scores
            result['anomaly_score'] = np.abs((df['value'] - rolling_mean) / (rolling_std + 1e-10))
            result['is_anomaly'] = result['anomaly_score'] > 3.0  # Threshold for deviation
        else:
            logger.warning(f"Unknown method: {self.method}")
            result['anomaly_score'] = 0
            result['is_anomaly'] = False
            
        return result

    def detect_anomalies_with_context(self, time_series, context_window=7):
        """
        Detect anomalies with contextual information

        Args:
            time_series: Time series data
            context_window: Number of days to consider for context

        Returns:
            DataFrame with anomaly scores, labels, and context
        """
        # Detect basic anomalies
        anomalies = self.detect_anomalies(time_series)
        
        if anomalies.empty:
            return pd.DataFrame()
            
        # Add contextual information
        result = anomalies.copy()
        
        # Add day of week context
        if isinstance(result.index, pd.DatetimeIndex):
            result['day_of_week'] = result.index.dayofweek
            
            # Calculate average by day of week
            day_of_week_avg = result.groupby('day_of_week')['value'].mean()
            day_of_week_std = result.groupby('day_of_week')['value'].std()
            
            # Calculate contextual anomaly score
            result['contextual_score'] = result.apply(
                lambda row: np.abs((row['value'] - day_of_week_avg[row['day_of_week']]) / 
                                  (day_of_week_std[row['day_of_week']] + 1e-10)),
                axis=1
            )
            
            # Determine if contextual anomaly
            result['is_contextual_anomaly'] = result['contextual_score'] > 3.0
            
            # Combine anomaly scores
            result['combined_score'] = (result['anomaly_score'] + result['contextual_score']) / 2
            result['is_combined_anomaly'] = result['is_anomaly'] | result['is_contextual_anomaly']
        
        return result

    def detect_change_points(self, time_series, window_size=7, threshold=2.0):
        """
        Detect change points in time series data

        Args:
            time_series: Time series data
            window_size: Size of the sliding window
            threshold: Threshold for change point detection

        Returns:
            DataFrame with change point scores and labels
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
        
        # Initialize change point scores
        result['change_point_score'] = 0.0
        result['is_change_point'] = False
        
        # Calculate change points
        if len(df) > window_size * 2:
            for i in range(window_size, len(df) - window_size):
                # Get windows
                window1 = df['value'].iloc[i-window_size:i]
                window2 = df['value'].iloc[i:i+window_size]
                
                # Calculate statistics
                mean1 = window1.mean()
                mean2 = window2.mean()
                std1 = window1.std()
                std2 = window2.std()
                
                # Calculate change point score
                if std1 > 0 and std2 > 0:
                    score = np.abs(mean2 - mean1) / np.sqrt(std1**2 + std2**2)
                else:
                    score = np.abs(mean2 - mean1)
                    
                result['change_point_score'].iloc[i] = score
                result['is_change_point'].iloc[i] = score > threshold
        
        return result

    def detect_seasonal_anomalies(self, time_series, period=7):
        """
        Detect seasonal anomalies in time series data

        Args:
            time_series: Time series data
            period: Seasonality period (e.g., 7 for weekly)

        Returns:
            DataFrame with seasonal anomaly scores and labels
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
        
        # Initialize seasonal anomaly scores
        result['seasonal_score'] = 0.0
        result['is_seasonal_anomaly'] = False
        
        # Calculate seasonal anomalies
        if len(df) > period * 2:
            # Calculate seasonal component
            seasonal_means = {}
            seasonal_stds = {}
            
            if isinstance(df.index, pd.DatetimeIndex):
                # Group by day of week
                df['day_of_week'] = df.index.dayofweek
                seasonal_means = df.groupby('day_of_week')['value'].mean().to_dict()
                seasonal_stds = df.groupby('day_of_week')['value'].std().to_dict()
                
                # Calculate seasonal anomaly scores
                result['seasonal_score'] = df.apply(
                    lambda row: np.abs((row['value'] - seasonal_means[row['day_of_week']]) / 
                                      (seasonal_stds[row['day_of_week']] + 1e-10)),
                    axis=1
                )
                
                # Determine if seasonal anomaly
                result['is_seasonal_anomaly'] = result['seasonal_score'] > 3.0
            else:
                # Use modulo for non-datetime index
                for i in range(len(df)):
                    season = i % period
                    if season not in seasonal_means:
                        values = df['value'].iloc[season::period]
                        seasonal_means[season] = values.mean()
                        seasonal_stds[season] = values.std()
                        
                    # Calculate seasonal anomaly score
                    if seasonal_stds[season] > 0:
                        score = np.abs((df['value'].iloc[i] - seasonal_means[season]) / seasonal_stds[season])
                    else:
                        score = np.abs(df['value'].iloc[i] - seasonal_means[season])
                        
                    result['seasonal_score'].iloc[i] = score
                    result['is_seasonal_anomaly'].iloc[i] = score > 3.0
        
        return result

    def detect_burst_patterns(self, time_series, window_size=3, threshold=2.0):
        """
        Detect burst patterns in time series data

        Args:
            time_series: Time series data
            window_size: Size of the sliding window
            threshold: Threshold for burst detection

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
        if len(df) > window_size:
            # Calculate rolling statistics
            rolling_mean = df['value'].rolling(window=window_size, min_periods=1).mean()
            rolling_std = df['value'].rolling(window=window_size, min_periods=1).std()
            
            # Calculate burst scores
            result['burst_score'] = (df['value'] - rolling_mean) / (rolling_std + 1e-10)
            
            # Determine if burst
            result['is_burst'] = result['burst_score'] > threshold
            
            # Ensure bursts are increases, not decreases
            result.loc[df['value'] < rolling_mean, 'is_burst'] = False
        
        return result

    def combine_detection_methods(self, time_series):
        """
        Combine multiple detection methods

        Args:
            time_series: Time series data

        Returns:
            DataFrame with combined detection results
        """
        # Detect anomalies
        anomalies = self.detect_anomalies(time_series)
        
        # Detect change points
        change_points = self.detect_change_points(time_series)
        
        # Detect seasonal anomalies
        seasonal_anomalies = self.detect_seasonal_anomalies(time_series)
        
        # Detect burst patterns
        bursts = self.detect_burst_patterns(time_series)
        
        # Combine results
        result = anomalies.copy()
        result['change_point_score'] = change_points['change_point_score']
        result['is_change_point'] = change_points['is_change_point']
        result['seasonal_score'] = seasonal_anomalies['seasonal_score']
        result['is_seasonal_anomaly'] = seasonal_anomalies['is_seasonal_anomaly']
        result['burst_score'] = bursts['burst_score']
        result['is_burst'] = bursts['is_burst']
        
        # Calculate combined score
        result['combined_score'] = (
            result['anomaly_score'] + 
            result['change_point_score'] + 
            result['seasonal_score'] + 
            result['burst_score']
        ) / 4
        
        # Determine if combined event
        result['is_event'] = (
            result['is_anomaly'] | 
            result['is_change_point'] | 
            result['is_seasonal_anomaly'] | 
            result['is_burst']
        )
        
        return result
