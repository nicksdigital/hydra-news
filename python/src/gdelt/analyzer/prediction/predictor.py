#!/usr/bin/env python3
"""
GDELT Predictive Event Detector

This module provides the main class for predicting future events based on patterns in news coverage.
"""

import os
import logging
import json
from datetime import datetime, timedelta

from .base_predictor import BasePredictor
from .models import PredictionModels
from .visualizer import PredictionVisualizer
from .report_generator import PredictionReportGenerator

# Set up logging
logger = logging.getLogger(__name__)

class PredictiveEventDetector(BasePredictor):
    """Class for predicting future events based on patterns in news coverage"""

    def predict_entity_mentions(self, entity_text, days_to_predict=14,
                              start_date=None, end_date=None, output_dir="timelines",
                              evaluate_models=True):
        """
        Predict future mentions of an entity based on historical patterns

        Args:
            entity_text: Text of the entity to predict mentions for
            days_to_predict: Number of days to predict into the future
            start_date: Start date for historical data (None for all data)
            end_date: End date for historical data (None for all data)
            output_dir: Directory to save the output
            evaluate_models: Whether to evaluate models on historical data

        Returns:
            Dictionary with prediction results
        """
        logger.info(f"Predicting future mentions for entity: {entity_text}")

        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

        # Get articles for the entity
        articles_df = self.get_entity_articles(entity_text, start_date, end_date)
        if articles_df.empty:
            return None

        # Prepare time series
        time_series = self.prepare_time_series(articles_df)

        # Make predictions using multiple models
        predictions = {}

        # 1. ARIMA model
        try:
            arima_predictions = PredictionModels.predict_arima(time_series, days_to_predict)
            predictions['arima'] = arima_predictions
        except Exception as e:
            logger.error(f"Error in ARIMA prediction: {e}")

        # 2. Exponential Smoothing
        try:
            exp_predictions = PredictionModels.predict_exponential_smoothing(time_series, days_to_predict)
            predictions['exponential_smoothing'] = exp_predictions
        except Exception as e:
            logger.error(f"Error in Exponential Smoothing prediction: {e}")

        # 3. Linear Regression
        try:
            lr_predictions = PredictionModels.predict_linear_regression(time_series, days_to_predict)
            predictions['linear_regression'] = lr_predictions
        except Exception as e:
            logger.error(f"Error in Linear Regression prediction: {e}")

        # 4. Random Forest
        try:
            rf_predictions = PredictionModels.predict_random_forest(time_series, days_to_predict)
            predictions['random_forest'] = rf_predictions
        except Exception as e:
            logger.error(f"Error in Random Forest prediction: {e}")

        # 5. Support Vector Regression
        try:
            svr_predictions = PredictionModels.predict_svr(time_series, days_to_predict)
            predictions['svr'] = svr_predictions
        except Exception as e:
            logger.error(f"Error in SVR prediction: {e}")

        # Create ensemble prediction (average of all models)
        ensemble_predictions = PredictionModels.create_ensemble_prediction(predictions)

        # Create prediction visualization
        prediction_chart_path = os.path.join(
            output_dir,
            f"{entity_text.replace(' ', '_')}_prediction.png"
        )
        PredictionVisualizer.create_prediction_visualization(
            entity_text,
            time_series,
            predictions,
            ensemble_predictions,
            prediction_chart_path
        )

        # Create prediction results
        prediction_results = self.create_prediction_results(
            entity_text,
            time_series,
            predictions,
            ensemble_predictions,
            prediction_chart_path,
            days_to_predict
        )

        # Evaluate models if requested
        if evaluate_models and len(time_series) >= 30:
            try:
                model_evaluation = PredictionModels.evaluate_models(time_series)
                prediction_results['model_evaluation'] = model_evaluation

                # Create model evaluation visualization
                evaluation_chart_path = os.path.join(
                    output_dir,
                    f"{entity_text.replace(' ', '_')}_model_evaluation.png"
                )
                PredictionVisualizer.create_model_evaluation_visualization(
                    model_evaluation,
                    evaluation_chart_path
                )
                prediction_results['model_evaluation_chart'] = evaluation_chart_path
            except Exception as e:
                logger.error(f"Error in model evaluation: {e}")

        # Save prediction results
        prediction_json_path = self.save_prediction_results(prediction_results, output_dir)

        # Generate prediction report
        report_path = PredictionReportGenerator.generate_prediction_report(prediction_results, output_dir)
        prediction_results['report_path'] = report_path

        return prediction_results

    def predict_entity_events(self, entity_text, days_to_predict=14, event_threshold=3,
                            start_date=None, end_date=None, output_dir="timelines"):
        """
        Predict future events involving an entity based on historical patterns

        Args:
            entity_text: Text of the entity to predict events for
            days_to_predict: Number of days to predict into the future
            event_threshold: Threshold for predicting an event (number of mentions)
            start_date: Start date for historical data (None for all data)
            end_date: End date for historical data (None for all data)
            output_dir: Directory to save the output

        Returns:
            Dictionary with event prediction results
        """
        logger.info(f"Predicting future events for entity: {entity_text}")

        # Get mention predictions
        mention_predictions = self.predict_entity_mentions(
            entity_text,
            days_to_predict,
            start_date,
            end_date,
            output_dir
        )

        if not mention_predictions:
            return None

        # Identify predicted events (days with mentions above threshold)
        predicted_events = []

        # Use ensemble predictions
        ensemble_predictions = mention_predictions['predictions']['ensemble']

        for date_str, count in ensemble_predictions.items():
            if count >= event_threshold:
                # Check if this is a local peak
                is_peak = True
                date = datetime.strptime(date_str, '%Y-%m-%d').date()

                # Check previous day
                prev_day = (date - timedelta(days=1)).strftime('%Y-%m-%d')
                if prev_day in ensemble_predictions and ensemble_predictions[prev_day] >= count:
                    is_peak = False

                # Check next day
                next_day = (date + timedelta(days=1)).strftime('%Y-%m-%d')
                if next_day in ensemble_predictions and ensemble_predictions[next_day] >= count:
                    is_peak = False

                if is_peak:
                    predicted_events.append({
                        'date': date_str,
                        'predicted_mentions': count,
                        'confidence': min(1.0, count / (2 * event_threshold))  # Simple confidence score
                    })

        # Sort events by date
        predicted_events.sort(key=lambda x: x['date'])

        # Create event prediction visualization
        event_prediction_chart_path = os.path.join(
            output_dir,
            f"{entity_text.replace(' ', '_')}_event_prediction.png"
        )
        PredictionVisualizer.create_event_prediction_visualization(
            entity_text,
            mention_predictions,
            predicted_events,
            event_threshold,
            event_prediction_chart_path
        )

        # Create event prediction results
        event_prediction_results = {
            'entity': entity_text,
            'prediction_start_date': mention_predictions['prediction_start_date'],
            'prediction_end_date': mention_predictions['prediction_end_date'],
            'event_threshold': event_threshold,
            'predicted_events': predicted_events,
            'event_prediction_chart': event_prediction_chart_path
        }

        # Save event prediction results
        event_prediction_json_path = os.path.join(
            output_dir,
            f"{entity_text.replace(' ', '_')}_event_prediction.json"
        )
        with open(event_prediction_json_path, 'w') as f:
            json.dump(event_prediction_results, f, indent=2)

        logger.info(f"Saved event prediction results to {event_prediction_json_path}")

        # Generate event prediction report
        report_path = PredictionReportGenerator.generate_event_prediction_report(event_prediction_results, output_dir)
        event_prediction_results['report_path'] = report_path

        return event_prediction_results
