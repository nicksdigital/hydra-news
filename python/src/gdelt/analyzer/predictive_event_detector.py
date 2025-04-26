#!/usr/bin/env python3
"""
GDELT Predictive Event Detector

This module provides functions for predicting future events based on patterns in news coverage.
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import logging
import json
from collections import defaultdict
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from sklearn.linear_model import LinearRegression

# Set up logging
logger = logging.getLogger(__name__)

class PredictiveEventDetector:
    """Class for predicting future events based on patterns in news coverage"""

    def __init__(self, db_manager=None):
        """
        Initialize the predictive event detector

        Args:
            db_manager: DatabaseManager instance for accessing stored data
        """
        self.db_manager = db_manager

    def predict_entity_mentions(self, entity_text, days_to_predict=14,
                              start_date=None, end_date=None, output_dir="timelines"):
        """
        Predict future mentions of an entity based on historical patterns

        Args:
            entity_text: Text of the entity to predict mentions for
            days_to_predict: Number of days to predict into the future
            start_date: Start date for historical data (None for all data)
            end_date: End date for historical data (None for all data)
            output_dir: Directory to save the output

        Returns:
            Dictionary with prediction results
        """
        logger.info(f"Predicting future mentions for entity: {entity_text}")

        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

        # Get historical data for the entity
        if self.db_manager and self.db_manager.conn:
            # Get entity ID
            self.db_manager.cursor.execute(
                "SELECT id FROM entities WHERE text = ?",
                (entity_text,)
            )
            result = self.db_manager.cursor.fetchone()

            if not result:
                logger.warning(f"Entity '{entity_text}' not found in database")
                return None

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
                return None

            logger.info(f"Found {len(articles_df)} articles for entity '{entity_text}'")
        else:
            logger.warning("No database connection available")
            return None

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

        # Make predictions using multiple models
        predictions = {}

        # 1. ARIMA model
        try:
            arima_predictions = self._predict_arima(time_series, days_to_predict)
            predictions['arima'] = arima_predictions
        except Exception as e:
            logger.error(f"Error in ARIMA prediction: {e}")

        # 2. Exponential Smoothing
        try:
            exp_predictions = self._predict_exponential_smoothing(time_series, days_to_predict)
            predictions['exponential_smoothing'] = exp_predictions
        except Exception as e:
            logger.error(f"Error in Exponential Smoothing prediction: {e}")

        # 3. Linear Regression
        try:
            lr_predictions = self._predict_linear_regression(time_series, days_to_predict)
            predictions['linear_regression'] = lr_predictions
        except Exception as e:
            logger.error(f"Error in Linear Regression prediction: {e}")

        # Create ensemble prediction (average of all models)
        ensemble_predictions = {}
        for date in predictions.get('arima', {}).keys():
            values = []
            for model in predictions.keys():
                if date in predictions[model]:
                    values.append(predictions[model][date])

            if values:
                ensemble_predictions[date] = sum(values) / len(values)

        # Create prediction visualization
        prediction_chart_path = os.path.join(
            output_dir,
            f"{entity_text.replace(' ', '_')}_prediction.png"
        )
        self._create_prediction_visualization(
            entity_text,
            time_series,
            predictions,
            ensemble_predictions,
            prediction_chart_path
        )

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

        # Save prediction results
        prediction_json_path = os.path.join(
            output_dir,
            f"{entity_text.replace(' ', '_')}_prediction.json"
        )
        with open(prediction_json_path, 'w') as f:
            json.dump(prediction_results, f, indent=2)

        logger.info(f"Saved prediction results to {prediction_json_path}")

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
        self._create_event_prediction_visualization(
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

        return event_prediction_results

    def _predict_arima(self, time_series, days_to_predict):
        """
        Make predictions using ARIMA model

        Args:
            time_series: Time series of historical data
            days_to_predict: Number of days to predict

        Returns:
            Dictionary with predictions
        """
        # Create ARIMA model
        model = ARIMA(time_series, order=(5, 1, 0))
        model_fit = model.fit()

        # Make predictions
        forecast = model_fit.forecast(steps=days_to_predict)

        # Create prediction dictionary
        predictions = {}
        for i, value in enumerate(forecast):
            date = time_series.index[-1] + timedelta(days=i+1)
            predictions[date.strftime('%Y-%m-%d')] = max(0, value)  # Ensure non-negative

        return predictions

    def _predict_exponential_smoothing(self, time_series, days_to_predict):
        """
        Make predictions using Exponential Smoothing

        Args:
            time_series: Time series of historical data
            days_to_predict: Number of days to predict

        Returns:
            Dictionary with predictions
        """
        # Create Exponential Smoothing model
        model = ExponentialSmoothing(
            time_series,
            trend='add',
            seasonal='add',
            seasonal_periods=7  # Weekly seasonality
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

    def _predict_linear_regression(self, time_series, days_to_predict):
        """
        Make predictions using Linear Regression

        Args:
            time_series: Time series of historical data
            days_to_predict: Number of days to predict

        Returns:
            Dictionary with predictions
        """
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

    def _create_prediction_visualization(self, entity_text, time_series, predictions,
                                       ensemble_predictions, output_path):
        """Create a visualization of entity mention predictions"""
        # Set up the figure
        plt.figure(figsize=(14, 8))

        # Plot historical data
        plt.plot(time_series.index, time_series.values, 'b-',
                label='Historical Data', linewidth=2)

        # Plot predictions
        colors = {'arima': 'r', 'exponential_smoothing': 'g', 'linear_regression': 'c'}
        for model, model_predictions in predictions.items():
            dates = [datetime.strptime(d, '%Y-%m-%d').date() for d in model_predictions.keys()]
            values = list(model_predictions.values())
            plt.plot(dates, values, f'{colors.get(model, "m")}--',
                    label=f'{model.replace("_", " ").title()} Prediction', alpha=0.7)

        # Plot ensemble prediction
        if ensemble_predictions:
            dates = [datetime.strptime(d, '%Y-%m-%d').date() for d in ensemble_predictions.keys()]
            values = list(ensemble_predictions.values())
            plt.plot(dates, values, 'k-',
                    label='Ensemble Prediction', linewidth=2)

        # Add vertical line at prediction start
        plt.axvline(x=time_series.index[-1], color='gray', linestyle='--', alpha=0.7)

        # Set title and labels
        plt.title(f"Mention Predictions for '{entity_text}'", fontsize=16)
        plt.xlabel('Date', fontsize=12)
        plt.ylabel('Number of Mentions', fontsize=12)

        # Format x-axis
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        plt.gca().xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))
        plt.xticks(rotation=45, ha='right')

        # Add grid
        plt.grid(True, linestyle='--', alpha=0.7)

        # Add legend
        plt.legend()

        # Adjust layout
        plt.tight_layout()

        # Save the plot
        plt.savefig(output_path)
        plt.close()

        logger.info(f"Created prediction visualization for '{entity_text}' at {output_path}")

    def _create_event_prediction_visualization(self, entity_text, mention_predictions,
                                             predicted_events, event_threshold, output_path):
        """Create a visualization of entity event predictions"""
        # Set up the figure
        plt.figure(figsize=(14, 8))

        # Plot historical data
        historical_data = mention_predictions['historical_data']
        dates = []
        for d in historical_data.keys():
            try:
                # Try to parse date with different formats
                if ' ' in d:  # Contains time component
                    dates.append(datetime.strptime(d, '%Y-%m-%d %H:%M:%S').date())
                else:
                    dates.append(datetime.strptime(d, '%Y-%m-%d').date())
            except ValueError:
                logger.warning(f"Could not parse date: {d}")
                continue

        values = list(historical_data.values())
        plt.plot(dates, values, 'b-',
                label='Historical Data', linewidth=2, alpha=0.7)

        # Plot ensemble prediction
        ensemble_predictions = mention_predictions['predictions']['ensemble']
        dates = [datetime.strptime(d, '%Y-%m-%d').date() for d in ensemble_predictions.keys()]
        values = list(ensemble_predictions.values())
        plt.plot(dates, values, 'k-',
                label='Ensemble Prediction', linewidth=2)

        # Plot event threshold
        plt.axhline(y=event_threshold, color='r', linestyle='--',
                   label=f'Event Threshold ({event_threshold})', alpha=0.7)

        # Plot predicted events
        if predicted_events:
            event_dates = [datetime.strptime(e['date'], '%Y-%m-%d').date() for e in predicted_events]
            event_values = [e['predicted_mentions'] for e in predicted_events]
            plt.scatter(event_dates, event_values, color='r', s=100,
                       label='Predicted Events', zorder=5)

            # Add event labels
            for i, event in enumerate(predicted_events):
                date = datetime.strptime(event['date'], '%Y-%m-%d').date()
                value = event['predicted_mentions']
                confidence = event['confidence']

                plt.annotate(
                    f"Event {i+1}\nConf: {confidence:.2f}",
                    xy=(date, value),
                    xytext=(10, 10),
                    textcoords='offset points',
                    fontsize=9,
                    bbox=dict(boxstyle='round,pad=0.5', fc='yellow', alpha=0.5)
                )

        # Add vertical line at prediction start
        prediction_start = datetime.strptime(mention_predictions['prediction_start_date'], '%Y-%m-%d').date()
        plt.axvline(x=prediction_start, color='gray', linestyle='--', alpha=0.7)

        # Set title and labels
        plt.title(f"Event Predictions for '{entity_text}'", fontsize=16)
        plt.xlabel('Date', fontsize=12)
        plt.ylabel('Number of Mentions', fontsize=12)

        # Format x-axis
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        plt.gca().xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))
        plt.xticks(rotation=45, ha='right')

        # Add grid
        plt.grid(True, linestyle='--', alpha=0.7)

        # Add legend
        plt.legend()

        # Adjust layout
        plt.tight_layout()

        # Save the plot
        plt.savefig(output_path)
        plt.close()

        logger.info(f"Created event prediction visualization for '{entity_text}' at {output_path}")

def generate_prediction_report(prediction_results, output_dir="timelines"):
    """
    Generate a markdown report for entity mention predictions

    Args:
        prediction_results: Prediction results
        output_dir: Directory to save the report

    Returns:
        Path to the report file
    """
    if not prediction_results:
        logger.warning("No prediction results provided")
        return None

    entity = prediction_results['entity']

    # Create report content
    report = f"""# Prediction Report for '{entity}'

## Overview

This report provides predictions for future mentions of '{entity}' in news articles.

- **Historical Data Range**: {prediction_results['historical_start_date']} to {prediction_results['historical_end_date']}
- **Prediction Range**: {prediction_results['prediction_start_date']} to {prediction_results['prediction_end_date']}

## Prediction Visualization

![Prediction Chart]({entity.replace(' ', '_')}_prediction.png)

## Prediction Models

The predictions are generated using multiple models:

1. **ARIMA**: A time series forecasting model that accounts for autocorrelation in the data
2. **Exponential Smoothing**: A forecasting method that gives more weight to recent observations
3. **Linear Regression**: A simple trend-based prediction model
4. **Ensemble**: An average of all model predictions

## Predicted Mention Counts

| Date | ARIMA | Exponential Smoothing | Linear Regression | Ensemble |
|------|-------|------------------------|-------------------|----------|
"""

    # Add predictions
    arima_predictions = prediction_results['predictions']['arima']
    exp_predictions = prediction_results['predictions']['exponential_smoothing']
    lr_predictions = prediction_results['predictions']['linear_regression']
    ensemble_predictions = prediction_results['predictions']['ensemble']

    # Get all dates
    all_dates = sorted(ensemble_predictions.keys())

    for date in all_dates:
        arima_value = arima_predictions.get(date, 'N/A')
        exp_value = exp_predictions.get(date, 'N/A')
        lr_value = lr_predictions.get(date, 'N/A')
        ensemble_value = ensemble_predictions.get(date, 'N/A')

        if arima_value != 'N/A':
            arima_value = f"{arima_value:.2f}"
        if exp_value != 'N/A':
            exp_value = f"{exp_value:.2f}"
        if lr_value != 'N/A':
            lr_value = f"{lr_value:.2f}"
        if ensemble_value != 'N/A':
            ensemble_value = f"{ensemble_value:.2f}"

        report += f"| {date} | {arima_value} | {exp_value} | {lr_value} | {ensemble_value} |\n"

    report += """
## Interpretation

The prediction chart shows the historical mention pattern and the forecasted mentions for the entity.
The ensemble prediction (black line) represents the consensus forecast from all models.

### Key Observations:

"""

    # Add observations based on predictions
    historical_data = prediction_results['historical_data']
    historical_values = list(historical_data.values())

    # Calculate average historical mentions
    avg_historical = sum(historical_values) / len(historical_values) if historical_values else 0

    # Calculate average predicted mentions
    predicted_values = list(ensemble_predictions.values())
    avg_predicted = sum(predicted_values) / len(predicted_values) if predicted_values else 0

    # Add trend observation
    if avg_predicted > avg_historical * 1.2:
        report += f"- **Increasing Trend**: The model predicts an increase in mentions of '{entity}' in the near future.\n"
    elif avg_predicted < avg_historical * 0.8:
        report += f"- **Decreasing Trend**: The model predicts a decrease in mentions of '{entity}' in the near future.\n"
    else:
        report += f"- **Stable Trend**: The model predicts relatively stable mentions of '{entity}' in the near future.\n"

    # Add peak observation
    max_predicted = max(predicted_values) if predicted_values else 0
    max_date = max(ensemble_predictions.items(), key=lambda x: x[1])[0] if ensemble_predictions else 'N/A'

    if max_predicted > avg_historical * 1.5:
        report += f"- **Peak Detection**: A significant peak in mentions is predicted around {max_date}.\n"

    # Add reliability note
    report += """
### Note on Reliability:

These predictions are based on historical patterns and should be interpreted with caution.
Unexpected events or changes in news coverage can significantly affect actual outcomes.
"""

    # Save report
    report_path = os.path.join(output_dir, f"{entity.replace(' ', '_')}_prediction_report.md")
    with open(report_path, 'w') as f:
        f.write(report)

    logger.info(f"Generated prediction report for '{entity}' saved to {report_path}")

    return report_path

def generate_event_prediction_report(event_prediction_results, output_dir="timelines"):
    """
    Generate a markdown report for entity event predictions

    Args:
        event_prediction_results: Event prediction results
        output_dir: Directory to save the report

    Returns:
        Path to the report file
    """
    if not event_prediction_results:
        logger.warning("No event prediction results provided")
        return None

    entity = event_prediction_results['entity']

    # Create report content
    report = f"""# Event Prediction Report for '{entity}'

## Overview

This report provides predictions for future events involving '{entity}' in news articles.

- **Prediction Range**: {event_prediction_results['prediction_start_date']} to {event_prediction_results['prediction_end_date']}
- **Event Threshold**: {event_prediction_results['event_threshold']} mentions

## Event Prediction Visualization

![Event Prediction Chart]({entity.replace(' ', '_')}_event_prediction.png)

## Predicted Events

"""

    # Add predicted events
    predicted_events = event_prediction_results['predicted_events']

    if predicted_events:
        report += "| Date | Predicted Mentions | Confidence |\n"
        report += "|------|-------------------|------------|\n"

        for i, event in enumerate(predicted_events):
            report += f"| {event['date']} | {event['predicted_mentions']:.2f} | {event['confidence']:.2f} |\n"

        report += "\n### Event Details\n\n"

        for i, event in enumerate(predicted_events):
            report += f"#### Event {i+1}: {event['date']}\n\n"
            report += f"- **Predicted Mentions**: {event['predicted_mentions']:.2f}\n"
            report += f"- **Confidence**: {event['confidence']:.2f}\n"
            report += f"- **Interpretation**: "

            if event['confidence'] > 0.8:
                report += "High confidence in this event prediction.\n"
            elif event['confidence'] > 0.5:
                report += "Moderate confidence in this event prediction.\n"
            else:
                report += "Low confidence in this event prediction.\n"

            report += "\n"
    else:
        report += "No significant events predicted for this entity in the forecast period.\n"

    report += """
## Interpretation

The event prediction chart shows the historical mention pattern and the forecasted mentions for the entity.
Events are predicted when the forecasted mentions exceed the event threshold and form a local peak.

### Note on Reliability:

Event predictions are based on historical patterns and should be interpreted with caution.
The confidence score indicates the relative certainty of each prediction, but unexpected factors
can significantly affect actual outcomes.
"""

    # Save report
    report_path = os.path.join(output_dir, f"{entity.replace(' ', '_')}_event_prediction_report.md")
    with open(report_path, 'w') as f:
        f.write(report)

    logger.info(f"Generated event prediction report for '{entity}' saved to {report_path}")

    return report_path
