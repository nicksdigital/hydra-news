#!/usr/bin/env python3
"""
GDELT Prediction Visualizer

This module provides visualization functions for the GDELT Predictive Event Detector.
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import logging

# Set up logging
logger = logging.getLogger(__name__)

class PredictionVisualizer:
    """Class for visualizing predictions"""

    @staticmethod
    def create_prediction_visualization(entity_text, time_series, predictions,
                                      ensemble_predictions, output_path):
        """
        Create a visualization of entity mention predictions

        Args:
            entity_text: Text of the entity
            time_series: Time series of historical data
            predictions: Dictionary of predictions from different models
            ensemble_predictions: Dictionary of ensemble predictions
            output_path: Path to save the visualization

        Returns:
            Path to the saved visualization
        """
        # Set up the figure
        plt.figure(figsize=(14, 8))

        # Plot historical data
        plt.plot(time_series.index, time_series.values, 'b-',
                label='Historical Data', linewidth=2)

        # Plot predictions
        colors = {
            'arima': 'r', 
            'exponential_smoothing': 'g', 
            'linear_regression': 'c',
            'random_forest': 'm',
            'svr': 'y'
        }
        
        for model, model_predictions in predictions.items():
            if not model_predictions:
                continue
                
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
        
        return output_path

    @staticmethod
    def create_event_prediction_visualization(entity_text, mention_predictions,
                                            predicted_events, event_threshold, output_path):
        """
        Create a visualization of entity event predictions

        Args:
            entity_text: Text of the entity
            mention_predictions: Dictionary with mention predictions
            predicted_events: List of predicted events
            event_threshold: Threshold for predicting an event
            output_path: Path to save the visualization

        Returns:
            Path to the saved visualization
        """
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
        
        return output_path

    @staticmethod
    def create_model_evaluation_visualization(evaluation_results, output_path):
        """
        Create a visualization of model evaluation results

        Args:
            evaluation_results: Dictionary with evaluation results
            output_path: Path to save the visualization

        Returns:
            Path to the saved visualization
        """
        if not evaluation_results:
            logger.warning("No evaluation results to visualize")
            return None

        # Set up the figure
        plt.figure(figsize=(14, 8))

        # Get models and metrics
        models = list(evaluation_results.keys())
        metrics = list(evaluation_results[models[0]].keys())

        # Create subplots for each metric
        fig, axes = plt.subplots(1, len(metrics), figsize=(15, 5))

        for i, metric in enumerate(metrics):
            ax = axes[i]
            
            # Get values for this metric
            values = [evaluation_results[model][metric] for model in models]
            
            # Create bar chart
            bars = ax.bar(models, values)
            
            # Add value labels
            for bar in bars:
                height = bar.get_height()
                ax.annotate(f'{height:.3f}',
                            xy=(bar.get_x() + bar.get_width() / 2, height),
                            xytext=(0, 3),  # 3 points vertical offset
                            textcoords="offset points",
                            ha='center', va='bottom')
            
            # Set title and labels
            ax.set_title(f'{metric.upper()}')
            ax.set_xlabel('Model')
            ax.set_ylabel(metric.upper())
            
            # Rotate x-axis labels
            plt.setp(ax.get_xticklabels(), rotation=45, ha='right')

        # Adjust layout
        plt.tight_layout()

        # Save the plot
        plt.savefig(output_path)
        plt.close()

        logger.info(f"Created model evaluation visualization at {output_path}")
        
        return output_path
