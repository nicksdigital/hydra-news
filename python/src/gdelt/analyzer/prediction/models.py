#!/usr/bin/env python3
"""
GDELT Prediction Models

This module provides different prediction models for the GDELT Predictive Event Detector.
"""

import numpy as np
import pandas as pd
from datetime import timedelta
import logging
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.svm import SVR
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

# Set up logging
logger = logging.getLogger(__name__)

class PredictionModels:
    """Class for different prediction models"""

    @staticmethod
    def predict_arima(time_series, days_to_predict, order=(5, 1, 0)):
        """
        Make predictions using ARIMA model

        Args:
            time_series: Time series of historical data
            days_to_predict: Number of days to predict
            order: ARIMA model order (p, d, q)

        Returns:
            Dictionary with predictions
        """
        try:
            # Create ARIMA model
            model = ARIMA(time_series, order=order)
            model_fit = model.fit()

            # Make predictions
            forecast = model_fit.forecast(steps=days_to_predict)

            # Create prediction dictionary
            predictions = {}
            for i, value in enumerate(forecast):
                date = time_series.index[-1] + timedelta(days=i+1)
                predictions[date.strftime('%Y-%m-%d')] = max(0, value)  # Ensure non-negative

            return predictions
        except Exception as e:
            logger.error(f"Error in ARIMA prediction: {e}")
            return {}

    @staticmethod
    def predict_exponential_smoothing(time_series, days_to_predict, seasonal_periods=7):
        """
        Make predictions using Exponential Smoothing

        Args:
            time_series: Time series of historical data
            days_to_predict: Number of days to predict
            seasonal_periods: Number of periods in a season

        Returns:
            Dictionary with predictions
        """
        try:
            # Create Exponential Smoothing model
            model = ExponentialSmoothing(
                time_series,
                trend='add',
                seasonal='add',
                seasonal_periods=seasonal_periods  # Weekly seasonality
            )
            model_fit = model.fit()

            # Make predictions
            forecast = model_fit.forecast(days_to_predict)

            # Create prediction dictionary
            predictions = {}
            for i, value in enumerate(forecast):
                date = time_series.index[-1] + timedelta(days=i+1)
                predictions[date.strftime('%Y-%m-%d')] = max(0, value)  # Ensure non-negative

            return predictions
        except Exception as e:
            logger.error(f"Error in Exponential Smoothing prediction: {e}")
            return {}

    @staticmethod
    def predict_linear_regression(time_series, days_to_predict):
        """
        Make predictions using Linear Regression

        Args:
            time_series: Time series of historical data
            days_to_predict: Number of days to predict

        Returns:
            Dictionary with predictions
        """
        try:
            # Create features (days since start)
            X = np.array(range(len(time_series))).reshape(-1, 1)
            y = time_series.values

            # Create Linear Regression model
            model = LinearRegression()
            model.fit(X, y)

            # Make predictions
            X_pred = np.array(range(len(time_series), len(time_series) + days_to_predict)).reshape(-1, 1)
            forecast = model.predict(X_pred)

            # Create prediction dictionary
            predictions = {}
            for i, value in enumerate(forecast):
                date = time_series.index[-1] + timedelta(days=i+1)
                predictions[date.strftime('%Y-%m-%d')] = max(0, value)  # Ensure non-negative

            return predictions
        except Exception as e:
            logger.error(f"Error in Linear Regression prediction: {e}")
            return {}

    @staticmethod
    def predict_random_forest(time_series, days_to_predict, n_estimators=100, max_depth=10):
        """
        Make predictions using Random Forest

        Args:
            time_series: Time series of historical data
            days_to_predict: Number of days to predict
            n_estimators: Number of trees in the forest
            max_depth: Maximum depth of the trees

        Returns:
            Dictionary with predictions
        """
        try:
            # Create features with lag values
            X, y = PredictionModels._create_features_with_lags(time_series, lags=[1, 2, 3, 7])

            if len(X) < 10:  # Not enough data for meaningful prediction
                logger.warning("Not enough data for Random Forest prediction")
                return {}

            # Create Random Forest model
            model = RandomForestRegressor(n_estimators=n_estimators, max_depth=max_depth, random_state=42)
            model.fit(X, y)

            # Make predictions
            predictions = {}
            last_values = time_series[-7:].values  # Last 7 values for initial lags

            for i in range(days_to_predict):
                # Create features for prediction
                features = np.array([
                    last_values[-1],  # lag 1
                    last_values[-2] if len(last_values) > 1 else 0,  # lag 2
                    last_values[-3] if len(last_values) > 2 else 0,  # lag 3
                    last_values[-7] if len(last_values) > 6 else 0,  # lag 7
                ]).reshape(1, -1)

                # Predict next value
                prediction = model.predict(features)[0]
                prediction = max(0, prediction)  # Ensure non-negative

                # Add prediction to results
                date = time_series.index[-1] + timedelta(days=i+1)
                predictions[date.strftime('%Y-%m-%d')] = prediction

                # Update last values for next prediction
                last_values = np.append(last_values[1:], prediction)

            return predictions
        except Exception as e:
            logger.error(f"Error in Random Forest prediction: {e}")
            return {}

    @staticmethod
    def predict_svr(time_series, days_to_predict, kernel='rbf', C=1.0, gamma='scale'):
        """
        Make predictions using Support Vector Regression

        Args:
            time_series: Time series of historical data
            days_to_predict: Number of days to predict
            kernel: Kernel type
            C: Regularization parameter
            gamma: Kernel coefficient

        Returns:
            Dictionary with predictions
        """
        try:
            # Create features with lag values
            X, y = PredictionModels._create_features_with_lags(time_series, lags=[1, 2, 3, 7])

            if len(X) < 10:  # Not enough data for meaningful prediction
                logger.warning("Not enough data for SVR prediction")
                return {}

            # Create SVR model
            model = SVR(kernel=kernel, C=C, gamma=gamma)
            model.fit(X, y)

            # Make predictions
            predictions = {}
            last_values = time_series[-7:].values  # Last 7 values for initial lags

            for i in range(days_to_predict):
                # Create features for prediction
                features = np.array([
                    last_values[-1],  # lag 1
                    last_values[-2] if len(last_values) > 1 else 0,  # lag 2
                    last_values[-3] if len(last_values) > 2 else 0,  # lag 3
                    last_values[-7] if len(last_values) > 6 else 0,  # lag 7
                ]).reshape(1, -1)

                # Predict next value
                prediction = model.predict(features)[0]
                prediction = max(0, prediction)  # Ensure non-negative

                # Add prediction to results
                date = time_series.index[-1] + timedelta(days=i+1)
                predictions[date.strftime('%Y-%m-%d')] = prediction

                # Update last values for next prediction
                last_values = np.append(last_values[1:], prediction)

            return predictions
        except Exception as e:
            logger.error(f"Error in SVR prediction: {e}")
            return {}

    @staticmethod
    def create_ensemble_prediction(predictions):
        """
        Create an ensemble prediction from multiple models

        Args:
            predictions: Dictionary of predictions from different models

        Returns:
            Dictionary with ensemble predictions
        """
        ensemble_predictions = {}
        
        # Get all dates from all models
        all_dates = set()
        for model_predictions in predictions.values():
            all_dates.update(model_predictions.keys())
        
        # Calculate ensemble prediction for each date
        for date in all_dates:
            values = []
            for model in predictions.keys():
                if date in predictions[model]:
                    values.append(predictions[model][date])
            
            if values:
                ensemble_predictions[date] = sum(values) / len(values)
        
        return ensemble_predictions

    @staticmethod
    def evaluate_models(time_series, test_size=0.2, cv=5):
        """
        Evaluate different prediction models using cross-validation

        Args:
            time_series: Time series of historical data
            test_size: Proportion of data to use for testing
            cv: Number of cross-validation folds

        Returns:
            Dictionary with evaluation results
        """
        if len(time_series) < 30:  # Not enough data for meaningful evaluation
            logger.warning("Not enough data for model evaluation")
            return {}

        # Create features with lag values
        X, y = PredictionModels._create_features_with_lags(time_series, lags=[1, 2, 3, 7])

        # Create time series cross-validation
        tscv = TimeSeriesSplit(n_splits=cv)

        # Models to evaluate
        models = {
            'linear_regression': LinearRegression(),
            'random_forest': RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42),
            'svr': SVR(kernel='rbf', C=1.0, gamma='scale')
        }

        # Evaluation metrics
        metrics = {
            'mse': mean_squared_error,
            'mae': mean_absolute_error,
            'r2': r2_score
        }

        # Evaluate models
        results = {}
        for model_name, model in models.items():
            model_results = {metric: [] for metric in metrics}
            
            for train_index, test_index in tscv.split(X):
                X_train, X_test = X[train_index], X[test_index]
                y_train, y_test = y[train_index], y[test_index]
                
                # Train model
                model.fit(X_train, y_train)
                
                # Make predictions
                y_pred = model.predict(X_test)
                
                # Calculate metrics
                for metric_name, metric_func in metrics.items():
                    model_results[metric_name].append(metric_func(y_test, y_pred))
            
            # Average metrics across folds
            results[model_name] = {
                metric: np.mean(values) for metric, values in model_results.items()
            }

        return results

    @staticmethod
    def _create_features_with_lags(time_series, lags=[1, 2, 3, 7]):
        """
        Create features with lag values for time series prediction

        Args:
            time_series: Time series of historical data
            lags: List of lag values to use as features

        Returns:
            X: Feature matrix
            y: Target values
        """
        # Create DataFrame from time series
        df = pd.DataFrame(time_series)
        df.columns = ['value']
        
        # Create lag features
        for lag in lags:
            df[f'lag_{lag}'] = df['value'].shift(lag)
        
        # Drop rows with NaN values
        df = df.dropna()
        
        # Create feature matrix and target values
        X = df.drop('value', axis=1).values
        y = df['value'].values
        
        return X, y
