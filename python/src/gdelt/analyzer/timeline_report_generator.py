#!/usr/bin/env python3
"""
GDELT Timeline Report Generator

This module provides functions for generating reports for advanced timeline features.
"""

import os
import logging
import json
from datetime import datetime

# Set up logging
logger = logging.getLogger(__name__)

def generate_event_sentiment_report(sentiment_results, output_dir="timelines"):
    """
    Generate a markdown report for event sentiment analysis

    Args:
        sentiment_results: Sentiment analysis results
        output_dir: Directory to save the report

    Returns:
        Path to the report file
    """
    if not sentiment_results:
        logger.warning("No sentiment results provided")
        return None

    entity = sentiment_results['entity']

    # Check if this is event sentiment or general sentiment over time
    is_event_sentiment = 'event_start_date' in sentiment_results

    # Create report content
    if is_event_sentiment:
        title = f"# Sentiment Analysis Report for '{entity}' during Event"
        period_text = f"**Event Period**: {sentiment_results['event_start_date']} to {sentiment_results['event_end_date']}"
    else:
        title = f"# Sentiment Analysis Report for '{entity}' over Time"
        period_text = f"**Time Period**: {sentiment_results['start_date']} to {sentiment_results['end_date']}"

    report = f"""{title}

## Overview

- {period_text}
- **Total Articles**: {sentiment_results['article_count']}
- **Overall Sentiment**: {sentiment_results['sentiment_stats']['mean']:.2f} (on a scale from -1 to 1)

## Sentiment Distribution

- **Positive Articles**: {sentiment_results['sentiment_stats']['positive_count']} ({sentiment_results['sentiment_stats']['positive_count'] / sentiment_results['article_count'] * 100:.1f}%)
- **Neutral Articles**: {sentiment_results['sentiment_stats']['neutral_count']} ({sentiment_results['sentiment_stats']['neutral_count'] / sentiment_results['article_count'] * 100:.1f}%)
- **Negative Articles**: {sentiment_results['sentiment_stats']['negative_count']} ({sentiment_results['sentiment_stats']['negative_count'] / sentiment_results['article_count'] * 100:.1f}%)

## Sentiment Visualization

![Sentiment Chart]({entity.replace(' ', '_')}_{'event_sentiment' if is_event_sentiment else 'sentiment_timeline'}.png)

## Sentiment by Source

| Source | Sentiment Score |
|--------|----------------|
"""

    # Add source sentiment
    for source, score in sentiment_results['source_sentiment'].items():
        report += f"| {source} | {score:.2f} |\n"

    report += """
## Articles by Sentiment

### Positive Articles

| Date | Source | Title | Sentiment |
|------|--------|-------|-----------|
"""

    # Add positive articles if available
    if 'articles_with_sentiment' in sentiment_results:
        positive_articles = [a for a in sentiment_results['articles_with_sentiment']
                            if a['sentiment_category'] == 'positive']
        for article in positive_articles[:5]:  # Limit to top 5
            report += f"| {article['date']} | {article['source']} | [{article['title']}]({article['url']}) | {article['sentiment_score']:.2f} |\n"
    else:
        report += "No detailed article sentiment data available.\n"

    report += """
### Negative Articles

| Date | Source | Title | Sentiment |
|------|--------|-------|-----------|
"""

    # Add negative articles if available
    if 'articles_with_sentiment' in sentiment_results:
        negative_articles = [a for a in sentiment_results['articles_with_sentiment']
                            if a['sentiment_category'] == 'negative']
        for article in negative_articles[:5]:  # Limit to top 5
            report += f"| {article['date']} | {article['source']} | [{article['title']}]({article['url']}) | {article['sentiment_score']:.2f} |\n"
    else:
        report += "No detailed article sentiment data available.\n"

    report += """
## Sentiment Timeline

The chart shows how sentiment towards the entity changed during the event period. Positive values indicate positive sentiment, while negative values indicate negative sentiment.

## Interpretation

"""

    # Add interpretation based on sentiment statistics
    mean_sentiment = sentiment_results['sentiment_stats']['mean']
    if mean_sentiment > 0.2:
        report += f"The overall sentiment towards '{entity}' during this event was very positive (score: {mean_sentiment:.2f}). "
    elif mean_sentiment > 0.05:
        report += f"The overall sentiment towards '{entity}' during this event was slightly positive (score: {mean_sentiment:.2f}). "
    elif mean_sentiment > -0.05:
        report += f"The overall sentiment towards '{entity}' during this event was neutral (score: {mean_sentiment:.2f}). "
    elif mean_sentiment > -0.2:
        report += f"The overall sentiment towards '{entity}' during this event was slightly negative (score: {mean_sentiment:.2f}). "
    else:
        report += f"The overall sentiment towards '{entity}' during this event was very negative (score: {mean_sentiment:.2f}). "

    # Add interpretation based on sentiment distribution
    positive_pct = sentiment_results['sentiment_stats']['positive_count'] / sentiment_results['article_count'] * 100
    negative_pct = sentiment_results['sentiment_stats']['negative_count'] / sentiment_results['article_count'] * 100

    if positive_pct > 60:
        report += f"A large majority ({positive_pct:.1f}%) of articles expressed positive sentiment. "
    elif positive_pct > negative_pct:
        report += f"More articles expressed positive sentiment ({positive_pct:.1f}%) than negative sentiment ({negative_pct:.1f}%). "
    elif negative_pct > 60:
        report += f"A large majority ({negative_pct:.1f}%) of articles expressed negative sentiment. "
    elif negative_pct > positive_pct:
        report += f"More articles expressed negative sentiment ({negative_pct:.1f}%) than positive sentiment ({positive_pct:.1f}%). "
    else:
        report += f"Articles were evenly split between positive and negative sentiment. "

    # Save report
    report_path = os.path.join(output_dir, f"{entity.replace(' ', '_')}_event_sentiment_report.md")
    with open(report_path, 'w') as f:
        f.write(report)

    logger.info(f"Generated event sentiment report for '{entity}' saved to {report_path}")

    return report_path

def generate_cross_entity_report(cross_entity_data, output_dir="timelines"):
    """
    Generate a markdown report for cross-entity analysis

    Args:
        cross_entity_data: Cross-entity analysis results
        output_dir: Directory to save the report

    Returns:
        Path to the report file
    """
    if not cross_entity_data:
        logger.warning("No cross-entity data provided")
        return None

    entity_list = cross_entity_data['entities']

    # Create report content
    report = f"""# Cross-Entity Analysis Report

## Overview

This report analyzes the relationships and events involving the following entities:
{', '.join(entity_list)}

## Entity Co-occurrences

The following visualization shows how often these entities are mentioned together in articles:

![Entity Network](entity_network_{'_'.join([e.replace(' ', '_') for e in entity_list[:3]])}.png)

![Entity Matrix](entity_matrix_{'_'.join([e.replace(' ', '_') for e in entity_list[:3]])}.png)

## Cross-Entity Events

The timeline below shows significant events involving multiple entities:

![Cross-Entity Events](cross_entity_events_{'_'.join([e.replace(' ', '_') for e in entity_list[:3]])}.png)

## Significant Events

"""

    # Add events
    if 'events' in cross_entity_data:
        for i, event in enumerate(cross_entity_data['events']):
            # Get top entity pair
            top_pair = max(event['entity_pairs'].items(), key=lambda x: x[1]) if event['entity_pairs'] else ('Unknown', 0)

            report += f"### Event {i+1}: {top_pair[0]}\n\n"
            report += f"- **Date Range**: {event['start_date']} to {event['end_date']}\n"
            report += f"- **Peak Date**: {event['peak_date']}\n"
            report += f"- **Article Count**: {event['article_count']} (Peak: {event['peak_count']})\n\n"

            report += "#### Entities Involved\n\n"
            for entity, count in event['entity_counts'].items():
                report += f"- {entity}: {count} articles\n"

            report += "\n#### Entity Pairs\n\n"
            for pair, count in event['entity_pairs'].items():
                report += f"- {pair}: {count} articles\n"

            report += "\n#### Top Themes\n\n"
            for theme, count in event['themes'].items():
                report += f"- {theme}: {count} articles\n"

            report += "\n#### Top Sources\n\n"
            for source, count in event['sources'].items():
                report += f"- {source}: {count} articles\n"

            report += "\n#### Key Articles\n\n"
            for article in event['top_articles']:
                entities_str = ', '.join(article['entities'])
                report += f"- [{article['title']}]({article['url']}) - {article['source']} ({article['date']}, Trust: {article['trust_score']:.2f})\n"
                report += f"  - Entities: {entities_str}\n"

            report += "\n"

    # Save report
    report_path = os.path.join(output_dir, f"cross_entity_report_{'_'.join([e.replace(' ', '_') for e in entity_list[:3]])}.md")
    with open(report_path, 'w') as f:
        f.write(report)

    logger.info(f"Generated cross-entity report saved to {report_path}")

    return report_path

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

def generate_sentiment_comparison_report(entity_list, sentiment_data, visualizations, output_dir="timelines"):
    """
    Generate a markdown report for sentiment comparison across multiple entities

    Args:
        entity_list: List of entities to compare
        sentiment_data: Dictionary with sentiment data for each entity
        visualizations: Dictionary with paths to visualization files
        output_dir: Directory to save the report

    Returns:
        Path to the report file
    """
    # Create report content
    report = f"""# Sentiment Comparison Report

## Overview

This report compares sentiment towards multiple entities in news articles:
{', '.join(entity_list)}

## Sentiment Timeline Comparison

The following chart shows how sentiment towards each entity changed over time:

![Sentiment Comparison]({os.path.basename(visualizations.get('comparison', ''))})

## Sentiment Heatmap

The heatmap below shows sentiment towards each entity over time, with red indicating negative sentiment and blue indicating positive sentiment:

![Sentiment Heatmap]({os.path.basename(visualizations.get('heatmap', ''))})

## Sentiment Distribution

The following chart shows the distribution of sentiment for each entity:

![Sentiment Distribution]({os.path.basename(visualizations.get('distribution', ''))})

## Entity Sentiment Summary

"""

    # Add entity sentiment summary
    for entity in entity_list:
        if entity not in sentiment_data:
            continue

        entity_sentiment = sentiment_data[entity]

        report += f"### {entity}\n\n"

        if 'sentiment_stats' in entity_sentiment:
            stats = entity_sentiment['sentiment_stats']
            report += f"- **Overall Sentiment**: {stats['mean']:.2f}\n"
            report += f"- **Positive Days**: {stats['positive_count']} ({stats['positive_count'] / (stats['positive_count'] + stats['neutral_count'] + stats['negative_count']) * 100:.1f}%)\n"
            report += f"- **Neutral Days**: {stats['neutral_count']} ({stats['neutral_count'] / (stats['positive_count'] + stats['neutral_count'] + stats['negative_count']) * 100:.1f}%)\n"
            report += f"- **Negative Days**: {stats['negative_count']} ({stats['negative_count'] / (stats['positive_count'] + stats['neutral_count'] + stats['negative_count']) * 100:.1f}%)\n"

        report += "\n"

    report += """
## Comparative Analysis

"""

    # Add comparative analysis
    entity_means = {}
    for entity in entity_list:
        if entity in sentiment_data and 'sentiment_stats' in sentiment_data[entity]:
            entity_means[entity] = sentiment_data[entity]['sentiment_stats']['mean']

    if entity_means:
        # Find most positive and negative entities
        most_positive = max(entity_means.items(), key=lambda x: x[1])
        most_negative = min(entity_means.items(), key=lambda x: x[1])

        report += f"- **Most Positive Coverage**: {most_positive[0]} (Score: {most_positive[1]:.2f})\n"
        report += f"- **Most Negative Coverage**: {most_negative[0]} (Score: {most_negative[1]:.2f})\n\n"

        # Add interpretation
        report += "### Interpretation\n\n"

        if most_positive[1] > 0.2 and most_negative[1] < -0.2:
            report += f"There is a significant contrast in media coverage between {most_positive[0]} (positive) and {most_negative[0]} (negative).\n"
        elif most_positive[1] > 0.1 and most_negative[1] < -0.1:
            report += f"There is a moderate contrast in media coverage between {most_positive[0]} (slightly positive) and {most_negative[0]} (slightly negative).\n"
        else:
            report += "The sentiment towards all entities is relatively similar, without strong positive or negative bias.\n"

    # Save report
    report_path = os.path.join(output_dir, f"sentiment_comparison_report_{'_'.join([e.replace(' ', '_') for e in entity_list[:3]])}.md")
    with open(report_path, 'w') as f:
        f.write(report)

    logger.info(f"Generated sentiment comparison report saved to {report_path}")

    return report_path

def generate_advanced_timeline_summary(entity_list, analysis_results, output_dir="timelines"):
    """
    Generate a summary report for all advanced timeline features

    Args:
        entity_list: List of entities analyzed
        analysis_results: Dictionary with all analysis results
        output_dir: Directory to save the report

    Returns:
        Path to the report file
    """
    # Create report content
    report = f"""# Advanced Timeline Analysis Summary

## Overview

This report summarizes the advanced timeline analysis for the following entities:
{', '.join(entity_list)}

## Analysis Features

The following advanced features were used to analyze the entities:

1. **Sentiment Analysis by Event**: Analysis of sentiment towards entities during specific events
2. **Cross-Entity Event Analysis**: Identification of events involving multiple entities
3. **Predictive Event Detection**: Prediction of future events based on patterns in news coverage

## Entity Reports

"""

    # Add entity reports
    for entity in entity_list:
        report += f"### {entity}\n\n"

        # Add sentiment analysis reports
        if 'sentiment' in analysis_results and entity in analysis_results['sentiment']:
            sentiment_report = f"{entity.replace(' ', '_')}_event_sentiment_report.md"
            report += f"- [Sentiment Analysis Report]({sentiment_report})\n"

        # Add prediction reports
        if 'predictions' in analysis_results and entity in analysis_results['predictions']:
            prediction_report = f"{entity.replace(' ', '_')}_prediction_report.md"
            report += f"- [Prediction Report]({prediction_report})\n"

            event_prediction_report = f"{entity.replace(' ', '_')}_event_prediction_report.md"
            report += f"- [Event Prediction Report]({event_prediction_report})\n"

        report += "\n"

    # Add cross-entity reports
    if 'cross_entity' in analysis_results:
        report += "## Cross-Entity Analysis\n\n"

        for i, cross_entity_result in enumerate(analysis_results['cross_entity']):
            entities = cross_entity_result.get('entities', [])
            if entities:
                report += f"### Group {i+1}: {', '.join(entities[:3])}{' and others' if len(entities) > 3 else ''}\n\n"

                cross_entity_report = f"cross_entity_report_{'_'.join([e.replace(' ', '_') for e in entities[:3]])}.md"
                report += f"- [Cross-Entity Analysis Report]({cross_entity_report})\n\n"

    # Add sentiment comparison reports
    if 'sentiment_comparison' in analysis_results:
        report += "## Sentiment Comparison\n\n"

        for i, comparison_result in enumerate(analysis_results['sentiment_comparison']):
            entities = comparison_result.get('entities', [])
            if entities:
                report += f"### Comparison {i+1}: {', '.join(entities[:3])}{' and others' if len(entities) > 3 else ''}\n\n"

                comparison_report = f"sentiment_comparison_report_{'_'.join([e.replace(' ', '_') for e in entities[:3]])}.md"
                report += f"- [Sentiment Comparison Report]({comparison_report})\n\n"

    # Save report
    report_path = os.path.join(output_dir, "advanced_timeline_summary.md")
    with open(report_path, 'w') as f:
        f.write(report)

    logger.info(f"Generated advanced timeline summary saved to {report_path}")

    return report_path
