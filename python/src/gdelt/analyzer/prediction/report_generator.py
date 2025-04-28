#!/usr/bin/env python3
"""
GDELT Prediction Report Generator

This module provides report generation functions for the GDELT Predictive Event Detector.
"""

import os
import logging
import numpy as np

# Set up logging
logger = logging.getLogger(__name__)

class PredictionReportGenerator:
    """Class for generating prediction reports"""

    @staticmethod
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
4. **Random Forest**: An ensemble learning method that builds multiple decision trees
5. **Support Vector Regression**: A machine learning method that uses support vector machines for regression
6. **Ensemble**: An average of all model predictions

## Predicted Mention Counts

| Date | ARIMA | Exponential Smoothing | Linear Regression | Random Forest | SVR | Ensemble |
|------|-------|------------------------|-------------------|---------------|-----|----------|
"""

        # Add predictions
        arima_predictions = prediction_results['predictions'].get('arima', {})
        exp_predictions = prediction_results['predictions'].get('exponential_smoothing', {})
        lr_predictions = prediction_results['predictions'].get('linear_regression', {})
        rf_predictions = prediction_results['predictions'].get('random_forest', {})
        svr_predictions = prediction_results['predictions'].get('svr', {})
        ensemble_predictions = prediction_results['predictions'].get('ensemble', {})

        # Get all dates
        all_dates = sorted(ensemble_predictions.keys())

        for date in all_dates:
            arima_value = arima_predictions.get(date, 'N/A')
            exp_value = exp_predictions.get(date, 'N/A')
            lr_value = lr_predictions.get(date, 'N/A')
            rf_value = rf_predictions.get(date, 'N/A')
            svr_value = svr_predictions.get(date, 'N/A')
            ensemble_value = ensemble_predictions.get(date, 'N/A')

            if arima_value != 'N/A':
                arima_value = f"{arima_value:.2f}"
            if exp_value != 'N/A':
                exp_value = f"{exp_value:.2f}"
            if lr_value != 'N/A':
                lr_value = f"{lr_value:.2f}"
            if rf_value != 'N/A':
                rf_value = f"{rf_value:.2f}"
            if svr_value != 'N/A':
                svr_value = f"{svr_value:.2f}"
            if ensemble_value != 'N/A':
                ensemble_value = f"{ensemble_value:.2f}"

            report += f"| {date} | {arima_value} | {exp_value} | {lr_value} | {rf_value} | {svr_value} | {ensemble_value} |\n"

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

        # Add volatility observation
        if predicted_values:
            volatility = np.std(predicted_values) / avg_predicted if avg_predicted > 0 else 0
            historical_volatility = np.std(historical_values) / avg_historical if avg_historical > 0 else 0
            
            if volatility > historical_volatility * 1.5:
                report += f"- **High Volatility**: The predictions show higher volatility than historical patterns, suggesting uncertainty.\n"
            elif volatility < historical_volatility * 0.5:
                report += f"- **Low Volatility**: The predictions show lower volatility than historical patterns, suggesting stability.\n"

        # Add reliability note
        report += """
### Note on Reliability:

These predictions are based on historical patterns and should be interpreted with caution.
Unexpected events or changes in news coverage can significantly affect actual outcomes.
"""

        # Add model evaluation if available
        if 'model_evaluation' in prediction_results:
            report += """
## Model Evaluation

The following table shows the performance of each model on historical data:

| Model | Mean Squared Error | Mean Absolute Error | R² Score |
|-------|-------------------|---------------------|----------|
"""
            
            for model, metrics in prediction_results['model_evaluation'].items():
                mse = metrics.get('mse', 'N/A')
                mae = metrics.get('mae', 'N/A')
                r2 = metrics.get('r2', 'N/A')
                
                if mse != 'N/A':
                    mse = f"{mse:.4f}"
                if mae != 'N/A':
                    mae = f"{mae:.4f}"
                if r2 != 'N/A':
                    r2 = f"{r2:.4f}"
                
                report += f"| {model.replace('_', ' ').title()} | {mse} | {mae} | {r2} |\n"
            
            report += """
Lower MSE and MAE values indicate better performance. Higher R² scores (closer to 1.0) indicate better fit.
"""

        # Save report
        report_path = os.path.join(output_dir, f"{entity.replace(' ', '_')}_prediction_report.md")
        with open(report_path, 'w') as f:
            f.write(report)

        logger.info(f"Generated prediction report for '{entity}' saved to {report_path}")

        return report_path

    @staticmethod
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
