#!/usr/bin/env python3
"""
GDELT Prediction Model Hyperparameter Tuning

This module provides functionality for tuning prediction model hyperparameters.
"""

import numpy as np
import pandas as pd
import logging
from sklearn.model_selection import TimeSeriesSplit, GridSearchCV, RandomizedSearchCV
from sklearn.linear_model import LinearRegression, Ridge, Lasso, ElasticNet
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.svm import SVR
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.preprocessing import StandardScaler
from joblib import dump, load
import os

# Set up logging
logger = logging.getLogger(__name__)

class HyperparameterTuner:
    """Class for tuning prediction model hyperparameters"""

    def __init__(self, output_dir="models"):
        """
        Initialize the hyperparameter tuner

        Args:
            output_dir: Directory to save tuned models
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def _create_features_with_lags(self, time_series, lags=[1, 2, 3, 7], add_date_features=True):
        """
        Create features with lag values and date features for time series prediction

        Args:
            time_series: Time series of historical data
            lags: List of lag values to use as features
            add_date_features: Whether to add date-based features

        Returns:
            X: Feature matrix
            y: Target values
            feature_names: List of feature names
        """
        # Create DataFrame from time series
        df = pd.DataFrame(time_series)
        df.columns = ['value']
        df.index = pd.to_datetime(df.index)
        
        # Create lag features
        for lag in lags:
            df[f'lag_{lag}'] = df['value'].shift(lag)
        
        # Add date-based features if requested
        if add_date_features:
            df['day_of_week'] = df.index.dayofweek
            df['day_of_month'] = df.index.day
            df['month'] = df.index.month
            df['quarter'] = df.index.quarter
            df['year'] = df.index.year
            df['is_weekend'] = df.index.dayofweek.isin([5, 6]).astype(int)
            
            # Add cyclical encoding for day of week
            df['day_of_week_sin'] = np.sin(2 * np.pi * df.index.dayofweek / 7)
            df['day_of_week_cos'] = np.cos(2 * np.pi * df.index.dayofweek / 7)
            
            # Add cyclical encoding for month
            df['month_sin'] = np.sin(2 * np.pi * df.index.month / 12)
            df['month_cos'] = np.cos(2 * np.pi * df.index.month / 12)
        
        # Add rolling statistics
        df['rolling_mean_7'] = df['value'].rolling(window=7, min_periods=1).mean()
        df['rolling_std_7'] = df['value'].rolling(window=7, min_periods=1).std()
        df['rolling_max_7'] = df['value'].rolling(window=7, min_periods=1).max()
        df['rolling_min_7'] = df['value'].rolling(window=7, min_periods=1).min()
        
        # Drop rows with NaN values
        df = df.dropna()
        
        # Create feature matrix and target values
        X = df.drop('value', axis=1).values
        y = df['value'].values
        feature_names = df.drop('value', axis=1).columns.tolist()
        
        return X, y, feature_names

    def tune_linear_models(self, time_series, cv=5, n_jobs=-1):
        """
        Tune linear regression models

        Args:
            time_series: Time series of historical data
            cv: Number of cross-validation folds
            n_jobs: Number of jobs to run in parallel

        Returns:
            Dictionary with tuned models
        """
        if len(time_series) < 30:  # Not enough data for meaningful tuning
            logger.warning("Not enough data for model tuning")
            return {}

        # Create features with lag values
        X, y, feature_names = self._create_features_with_lags(time_series)
        
        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Create time series cross-validation
        tscv = TimeSeriesSplit(n_splits=cv)
        
        # Models to tune
        models = {
            'ridge': {
                'model': Ridge(),
                'params': {
                    'alpha': [0.01, 0.1, 1.0, 10.0, 100.0],
                    'solver': ['auto', 'svd', 'cholesky', 'lsqr', 'sparse_cg', 'sag', 'saga']
                }
            },
            'lasso': {
                'model': Lasso(),
                'params': {
                    'alpha': [0.01, 0.1, 1.0, 10.0, 100.0],
                    'selection': ['cyclic', 'random']
                }
            },
            'elastic_net': {
                'model': ElasticNet(),
                'params': {
                    'alpha': [0.01, 0.1, 1.0, 10.0, 100.0],
                    'l1_ratio': [0.1, 0.3, 0.5, 0.7, 0.9],
                    'selection': ['cyclic', 'random']
                }
            }
        }
        
        # Tune models
        tuned_models = {}
        
        for name, config in models.items():
            logger.info(f"Tuning {name} model...")
            
            try:
                # Create grid search
                grid_search = GridSearchCV(
                    config['model'],
                    config['params'],
                    cv=tscv,
                    scoring='neg_mean_squared_error',
                    n_jobs=n_jobs,
                    verbose=1
                )
                
                # Fit grid search
                grid_search.fit(X_scaled, y)
                
                # Get best model
                best_model = grid_search.best_estimator_
                best_params = grid_search.best_params_
                best_score = -grid_search.best_score_  # Convert back to MSE
                
                logger.info(f"Best {name} model: {best_params}, MSE: {best_score:.4f}")
                
                # Save model
                model_path = os.path.join(self.output_dir, f"{name}_model.joblib")
                dump((best_model, scaler, feature_names), model_path)
                
                # Add to tuned models
                tuned_models[name] = {
                    'model': best_model,
                    'scaler': scaler,
                    'feature_names': feature_names,
                    'params': best_params,
                    'mse': best_score,
                    'path': model_path
                }
            except Exception as e:
                logger.error(f"Error tuning {name} model: {e}")
        
        return tuned_models

    def tune_tree_models(self, time_series, cv=5, n_jobs=-1, n_iter=20):
        """
        Tune tree-based regression models

        Args:
            time_series: Time series of historical data
            cv: Number of cross-validation folds
            n_jobs: Number of jobs to run in parallel
            n_iter: Number of iterations for randomized search

        Returns:
            Dictionary with tuned models
        """
        if len(time_series) < 30:  # Not enough data for meaningful tuning
            logger.warning("Not enough data for model tuning")
            return {}

        # Create features with lag values
        X, y, feature_names = self._create_features_with_lags(time_series)
        
        # Create time series cross-validation
        tscv = TimeSeriesSplit(n_splits=cv)
        
        # Models to tune
        models = {
            'random_forest': {
                'model': RandomForestRegressor(random_state=42),
                'params': {
                    'n_estimators': [50, 100, 200, 300, 500],
                    'max_depth': [None, 5, 10, 15, 20, 30],
                    'min_samples_split': [2, 5, 10],
                    'min_samples_leaf': [1, 2, 4],
                    'max_features': ['auto', 'sqrt', 'log2']
                }
            },
            'gradient_boosting': {
                'model': GradientBoostingRegressor(random_state=42),
                'params': {
                    'n_estimators': [50, 100, 200, 300, 500],
                    'learning_rate': [0.01, 0.05, 0.1, 0.2],
                    'max_depth': [3, 5, 7, 9],
                    'min_samples_split': [2, 5, 10],
                    'min_samples_leaf': [1, 2, 4],
                    'subsample': [0.8, 0.9, 1.0]
                }
            }
        }
        
        # Tune models
        tuned_models = {}
        
        for name, config in models.items():
            logger.info(f"Tuning {name} model...")
            
            try:
                # Create randomized search (more efficient for large parameter spaces)
                random_search = RandomizedSearchCV(
                    config['model'],
                    config['params'],
                    n_iter=n_iter,
                    cv=tscv,
                    scoring='neg_mean_squared_error',
                    n_jobs=n_jobs,
                    random_state=42,
                    verbose=1
                )
                
                # Fit randomized search
                random_search.fit(X, y)  # No need to scale for tree-based models
                
                # Get best model
                best_model = random_search.best_estimator_
                best_params = random_search.best_params_
                best_score = -random_search.best_score_  # Convert back to MSE
                
                logger.info(f"Best {name} model: {best_params}, MSE: {best_score:.4f}")
                
                # Save model
                model_path = os.path.join(self.output_dir, f"{name}_model.joblib")
                dump((best_model, None, feature_names), model_path)  # No scaler for tree-based models
                
                # Add to tuned models
                tuned_models[name] = {
                    'model': best_model,
                    'scaler': None,
                    'feature_names': feature_names,
                    'params': best_params,
                    'mse': best_score,
                    'path': model_path
                }
            except Exception as e:
                logger.error(f"Error tuning {name} model: {e}")
        
        return tuned_models

    def tune_svr_model(self, time_series, cv=5, n_jobs=-1, n_iter=20):
        """
        Tune Support Vector Regression model

        Args:
            time_series: Time series of historical data
            cv: Number of cross-validation folds
            n_jobs: Number of jobs to run in parallel
            n_iter: Number of iterations for randomized search

        Returns:
            Dictionary with tuned model
        """
        if len(time_series) < 30:  # Not enough data for meaningful tuning
            logger.warning("Not enough data for model tuning")
            return {}

        # Create features with lag values
        X, y, feature_names = self._create_features_with_lags(time_series)
        
        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Create time series cross-validation
        tscv = TimeSeriesSplit(n_splits=cv)
        
        # SVR parameters
        svr_params = {
            'kernel': ['linear', 'poly', 'rbf', 'sigmoid'],
            'C': [0.1, 1.0, 10.0, 100.0],
            'gamma': ['scale', 'auto', 0.01, 0.1, 1.0],
            'epsilon': [0.01, 0.1, 0.2, 0.5]
        }
        
        logger.info("Tuning SVR model...")
        
        try:
            # Create randomized search
            random_search = RandomizedSearchCV(
                SVR(),
                svr_params,
                n_iter=n_iter,
                cv=tscv,
                scoring='neg_mean_squared_error',
                n_jobs=n_jobs,
                random_state=42,
                verbose=1
            )
            
            # Fit randomized search
            random_search.fit(X_scaled, y)
            
            # Get best model
            best_model = random_search.best_estimator_
            best_params = random_search.best_params_
            best_score = -random_search.best_score_  # Convert back to MSE
            
            logger.info(f"Best SVR model: {best_params}, MSE: {best_score:.4f}")
            
            # Save model
            model_path = os.path.join(self.output_dir, "svr_model.joblib")
            dump((best_model, scaler, feature_names), model_path)
            
            # Return tuned model
            return {
                'svr': {
                    'model': best_model,
                    'scaler': scaler,
                    'feature_names': feature_names,
                    'params': best_params,
                    'mse': best_score,
                    'path': model_path
                }
            }
        except Exception as e:
            logger.error(f"Error tuning SVR model: {e}")
            return {}

    def tune_all_models(self, time_series, cv=5, n_jobs=-1, n_iter=20):
        """
        Tune all regression models

        Args:
            time_series: Time series of historical data
            cv: Number of cross-validation folds
            n_jobs: Number of jobs to run in parallel
            n_iter: Number of iterations for randomized search

        Returns:
            Dictionary with all tuned models
        """
        if len(time_series) < 30:  # Not enough data for meaningful tuning
            logger.warning("Not enough data for model tuning")
            return {}

        # Tune linear models
        linear_models = self.tune_linear_models(time_series, cv, n_jobs)
        
        # Tune tree models
        tree_models = self.tune_tree_models(time_series, cv, n_jobs, n_iter)
        
        # Tune SVR model
        svr_model = self.tune_svr_model(time_series, cv, n_jobs, n_iter)
        
        # Combine all models
        all_models = {}
        all_models.update(linear_models)
        all_models.update(tree_models)
        all_models.update(svr_model)
        
        # Find best model
        if all_models:
            best_model_name = min(all_models, key=lambda x: all_models[x]['mse'])
            best_model = all_models[best_model_name]
            
            logger.info(f"Best overall model: {best_model_name}, MSE: {best_model['mse']:.4f}")
            
            # Save best model info
            best_model_info = {
                'name': best_model_name,
                'params': best_model['params'],
                'mse': best_model['mse'],
                'path': best_model['path']
            }
            
            best_model_info_path = os.path.join(self.output_dir, "best_model_info.joblib")
            dump(best_model_info, best_model_info_path)
            
            all_models['best_model'] = best_model_info
        
        return all_models

    def predict_with_tuned_model(self, model_path, time_series, days_to_predict):
        """
        Make predictions using a tuned model

        Args:
            model_path: Path to the tuned model
            time_series: Time series of historical data
            days_to_predict: Number of days to predict

        Returns:
            Dictionary with predictions
        """
        try:
            # Load model
            model, scaler, feature_names = load(model_path)
            
            # Make predictions
            predictions = {}
            
            # Get the last values for features
            last_values = time_series[-max(7, max([int(f.split('_')[1]) for f in feature_names if f.startswith('lag_')]))-1:]
            
            for i in range(days_to_predict):
                # Create features for prediction
                features = self._create_prediction_features(last_values, feature_names)
                
                # Scale features if needed
                if scaler is not None:
                    features = scaler.transform(features.reshape(1, -1))
                
                # Predict next value
                prediction = model.predict(features.reshape(1, -1))[0]
                prediction = max(0, prediction)  # Ensure non-negative
                
                # Add prediction to results
                date = time_series.index[-1] + pd.Timedelta(days=i+1)
                predictions[date.strftime('%Y-%m-%d')] = prediction
                
                # Update last values for next prediction
                last_values = pd.concat([last_values[1:], pd.Series([prediction], index=[date])])
            
            return predictions
        except Exception as e:
            logger.error(f"Error predicting with tuned model: {e}")
            return {}

    def _create_prediction_features(self, last_values, feature_names):
        """
        Create features for prediction

        Args:
            last_values: Last values of the time series
            feature_names: List of feature names

        Returns:
            Feature vector
        """
        # Create features dictionary
        features = {}
        
        # Add lag features
        for feature in feature_names:
            if feature.startswith('lag_'):
                lag = int(feature.split('_')[1])
                if lag <= len(last_values):
                    features[feature] = last_values[-lag]
                else:
                    features[feature] = 0
            elif feature.startswith('rolling_'):
                # Add rolling statistics
                window = int(feature.split('_')[2])
                stat = feature.split('_')[1]
                
                if stat == 'mean':
                    features[feature] = last_values[-min(window, len(last_values)):].mean()
                elif stat == 'std':
                    features[feature] = last_values[-min(window, len(last_values)):].std() if len(last_values) > 1 else 0
                elif stat == 'max':
                    features[feature] = last_values[-min(window, len(last_values)):].max()
                elif stat == 'min':
                    features[feature] = last_values[-min(window, len(last_values)):].min()
            elif feature.startswith('day_of_week'):
                # Add day of week features
                date = last_values.index[-1] + pd.Timedelta(days=1)
                if feature == 'day_of_week':
                    features[feature] = date.dayofweek
                elif feature == 'day_of_week_sin':
                    features[feature] = np.sin(2 * np.pi * date.dayofweek / 7)
                elif feature == 'day_of_week_cos':
                    features[feature] = np.cos(2 * np.pi * date.dayofweek / 7)
            elif feature.startswith('month'):
                # Add month features
                date = last_values.index[-1] + pd.Timedelta(days=1)
                if feature == 'month':
                    features[feature] = date.month
                elif feature == 'month_sin':
                    features[feature] = np.sin(2 * np.pi * date.month / 12)
                elif feature == 'month_cos':
                    features[feature] = np.cos(2 * np.pi * date.month / 12)
            elif feature == 'day_of_month':
                date = last_values.index[-1] + pd.Timedelta(days=1)
                features[feature] = date.day
            elif feature == 'quarter':
                date = last_values.index[-1] + pd.Timedelta(days=1)
                features[feature] = (date.month - 1) // 3 + 1
            elif feature == 'year':
                date = last_values.index[-1] + pd.Timedelta(days=1)
                features[feature] = date.year
            elif feature == 'is_weekend':
                date = last_values.index[-1] + pd.Timedelta(days=1)
                features[feature] = 1 if date.dayofweek in [5, 6] else 0
        
        # Convert to numpy array in the same order as feature_names
        return np.array([features.get(feature, 0) for feature in feature_names])
