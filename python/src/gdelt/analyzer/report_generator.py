#!/usr/bin/env python3
"""
GDELT Report Generator

This module provides functions for generating reports from GDELT news data analysis.
"""

import os
import pandas as pd
import json
from datetime import datetime
import logging

# Set up logging
logger = logging.getLogger(__name__)

def generate_report(articles, themes, summary, analysis_results, output_dir):
    """
    Generate a markdown report of the analysis
    
    Args:
        articles: DataFrame containing articles
        themes: Dictionary mapping theme IDs to descriptions
        summary: Dictionary with summary information
        analysis_results: Dictionary with analysis results
        output_dir: Directory to save the report
    """
    logger.info("Generating report")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Extract analysis results
    theme_counts = analysis_results.get('theme_counts')
    date_counts = analysis_results.get('date_counts')
    hour_counts = analysis_results.get('hour_counts')
    day_counts = analysis_results.get('day_counts')
    domain_counts = analysis_results.get('domain_counts')
    tld_counts = analysis_results.get('tld_counts')
    language_counts = analysis_results.get('language_counts')
    country_counts = analysis_results.get('country_counts')
    theme_sentiment = analysis_results.get('theme_sentiment')
    source_diversity = analysis_results.get('source_diversity')
    topic_words = analysis_results.get('topic_words')
    
    # Generate report title and summary
    timespan = summary.get('timespan', '1 month')
    
    report = f"""# GDELT News Dataset Analysis ({timespan})

## Dataset Summary

- **Total Articles**: {summary.get('total_articles', len(articles))}
- **Total Themes**: {summary.get('total_themes', len(articles['theme_id'].unique()))}
- **Date Range**: {summary.get('date_range', {}).get('start_date', 'Unknown')} to {summary.get('date_range', {}).get('end_date', 'Unknown')} ({timespan})
- **Languages**: {', '.join(articles['language'].value_counts().head(5).index.tolist())}
- **Dataset Size**: {len(articles) * 10 / (1024 * 1024):.2f} GB (estimated)
- **Fetch Date**: {summary.get('fetch_date', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}

## Theme Distribution

The dataset contains articles from {len(articles['theme_id'].unique())} different themes. The top 10 themes are:

| Theme | Description | Count |
|-------|-------------|-------|
"""
    
    # Add top 10 themes
    if theme_counts is not None:
        for _, row in theme_counts.head(10).iterrows():
            report += f"| {row['theme_id']} | {row['description']} | {row['count']} |\n"
    
    report += """
## Temporal Analysis

### Articles by Date

The distribution of articles over the date range:

![Articles by Date](articles_by_date.png)

### Articles by Hour of Day

The distribution of articles by hour of the day:

![Articles by Hour](articles_by_hour.png)

### Articles by Day of Week

The distribution of articles by day of the week:

![Articles by Day](articles_by_day.png)

## Source Analysis

### Top Domains

The top 10 domains by article count:

| Domain | Count |
|--------|-------|
"""
    
    # Add top 10 domains
    if domain_counts is not None:
        for domain, count in domain_counts.head(10).items():
            report += f"| {domain} | {count} |\n"
    
    report += """
### Top TLDs

The top 5 top-level domains:

| TLD | Count |
|-----|-------|
"""
    
    # Add top 5 TLDs
    if tld_counts is not None:
        for tld, count in tld_counts.head(5).items():
            report += f"| {tld} | {count} |\n"
    
    report += """
### Language Distribution

The distribution of articles by language:

![Language Distribution](language_distribution.png)

### Country Distribution

The distribution of articles by source country:

![Country Distribution](country_distribution.png)
"""
    
    # Add source diversity if available
    if source_diversity is not None:
        report += """
### Source Diversity

The diversity of news sources in the dataset:

| Metric | Value |
|--------|-------|
"""
        report += f"| Unique Domains | {source_diversity.get('unique_domains', 'N/A')} |\n"
        report += f"| Unique Countries | {source_diversity.get('unique_countries', 'N/A')} |\n"
        report += f"| Unique Languages | {source_diversity.get('unique_languages', 'N/A')} |\n"
        report += f"| Domain Diversity Index | {source_diversity.get('domain_diversity', 'N/A'):.4f} |\n"
        report += f"| Country Diversity Index | {source_diversity.get('country_diversity', 'N/A'):.4f} |\n"
        report += f"| Language Diversity Index | {source_diversity.get('language_diversity', 'N/A'):.4f} |\n"
    
    report += """
## Theme Relationships

The correlation between the top themes:

![Theme Correlation](theme_correlation.png)
"""
    
    # Add sentiment analysis if available
    if theme_sentiment is not None:
        report += """
## Sentiment Analysis

### Sentiment Distribution

The distribution of sentiment polarity in article titles:

![Sentiment Polarity](sentiment_polarity.png)

### Sentiment by Theme

The sentiment polarity for the top themes:

![Sentiment by Theme](sentiment_by_theme.png)

### Top Positive and Negative Themes

The themes with the most positive and negative sentiment:

| Theme | Description | Average Sentiment | Article Count |
|-------|-------------|-------------------|---------------|
"""
        
        # Add top 5 positive themes
        for _, row in theme_sentiment.head(5).iterrows():
            report += f"| {row['theme_id']} | {row['theme_description']} | {row['sentiment_polarity_mean']:.4f} | {row['sentiment_polarity_count']} |\n"
        
        report += "\n"
        
        # Add top 5 negative themes
        for _, row in theme_sentiment.tail(5).iloc[::-1].iterrows():
            report += f"| {row['theme_id']} | {row['theme_description']} | {row['sentiment_polarity_mean']:.4f} | {row['sentiment_polarity_count']} |\n"
    
    # Add topic modeling if available
    if topic_words is not None:
        report += """
## Topic Modeling

### Discovered Topics

The main topics discovered in the article titles:

"""
        
        for topic_idx, words in enumerate(topic_words):
            report += f"**Topic {topic_idx + 1}**: {', '.join(words[:10])}\n\n"
            report += f"![Topic {topic_idx + 1} Word Cloud](topic_{topic_idx + 1}_wordcloud.png)\n\n"
    
    report += """
## Conclusion

This analysis provides an overview of the multilingual news dataset collected from GDELT. This dataset provides a comprehensive view of recent news coverage across multiple themes and sources in multiple languages.

### Benefits of the Multilingual Dataset

1. **Recent Coverage**: Focuses on the most recent and relevant news articles
2. **API Reliability**: Uses the officially supported timeframe for maximum data quality
3. **Source Diversity**: Captures a wide range of news sources and perspectives
4. **Theme Coverage**: Includes articles across numerous thematic categories
5. **Language Diversity**: Provides content in multiple languages for cross-lingual analysis
6. **Cultural Perspectives**: Offers different cultural viewpoints on the same news events
7. **Training Data**: Provides a substantial multilingual dataset for training machine learning models
8. **Current Events**: Reflects the current news landscape and emerging topics across language barriers

"""
    
    # Save the report
    report_path = os.path.join(output_dir, "report.md")
    with open(report_path, 'w') as f:
        f.write(report)
    
    logger.info(f"Generated report at {report_path}")
    return report_path

def generate_json_summary(analysis_results, output_dir):
    """
    Generate a JSON summary of the analysis
    
    Args:
        analysis_results: Dictionary with analysis results
        output_dir: Directory to save the summary
    """
    logger.info("Generating JSON summary")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Create a serializable summary
    summary = {}
    
    # Add theme counts
    if 'theme_counts' in analysis_results:
        summary['theme_counts'] = analysis_results['theme_counts'].head(20).to_dict(orient='records')
    
    # Add time patterns
    if 'date_counts' in analysis_results:
        summary['date_counts'] = {str(k): v for k, v in analysis_results['date_counts'].head(30).to_dict().items()}
    
    if 'hour_counts' in analysis_results:
        summary['hour_counts'] = analysis_results['hour_counts'].to_dict()
    
    if 'day_counts' in analysis_results:
        summary['day_counts'] = analysis_results['day_counts'].to_dict()
    
    # Add source distributions
    if 'domain_counts' in analysis_results:
        summary['domain_counts'] = analysis_results['domain_counts'].head(20).to_dict()
    
    if 'language_counts' in analysis_results:
        summary['language_counts'] = analysis_results['language_counts'].to_dict()
    
    if 'country_counts' in analysis_results:
        summary['country_counts'] = analysis_results['country_counts'].to_dict()
    
    # Add source diversity
    if 'source_diversity' in analysis_results:
        summary['source_diversity'] = analysis_results['source_diversity']
    
    # Add sentiment analysis
    if 'theme_sentiment' in analysis_results:
        summary['theme_sentiment'] = analysis_results['theme_sentiment'].head(10).to_dict(orient='records')
    
    # Add topic modeling
    if 'topic_words' in analysis_results:
        summary['topics'] = [
            {
                'topic_id': i + 1,
                'top_words': words[:10]
            }
            for i, words in enumerate(analysis_results['topic_words'])
        ]
    
    # Save the summary
    summary_path = os.path.join(output_dir, "analysis_summary.json")
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Generated JSON summary at {summary_path}")
    return summary_path

def generate_csv_exports(articles, analysis_results, output_dir):
    """
    Generate CSV exports of the analysis results
    
    Args:
        articles: DataFrame containing articles
        analysis_results: Dictionary with analysis results
        output_dir: Directory to save the exports
    """
    logger.info("Generating CSV exports")
    
    # Create output directory
    exports_dir = os.path.join(output_dir, "exports")
    os.makedirs(exports_dir, exist_ok=True)
    
    # Export theme counts
    if 'theme_counts' in analysis_results:
        theme_counts_path = os.path.join(exports_dir, "theme_counts.csv")
        analysis_results['theme_counts'].to_csv(theme_counts_path, index=False)
        logger.info(f"Exported theme counts to {theme_counts_path}")
    
    # Export time patterns
    if 'date_counts' in analysis_results:
        date_counts_path = os.path.join(exports_dir, "date_counts.csv")
        analysis_results['date_counts'].reset_index().to_csv(date_counts_path, index=False)
        logger.info(f"Exported date counts to {date_counts_path}")
    
    # Export sentiment analysis
    if 'sentiment_df' in analysis_results:
        sentiment_path = os.path.join(exports_dir, "sentiment_analysis.csv")
        analysis_results['sentiment_df'][['url', 'title', 'theme_id', 'sentiment_polarity', 'sentiment_subjectivity']].to_csv(sentiment_path, index=False)
        logger.info(f"Exported sentiment analysis to {sentiment_path}")
    
    # Export theme sentiment
    if 'theme_sentiment' in analysis_results:
        theme_sentiment_path = os.path.join(exports_dir, "theme_sentiment.csv")
        analysis_results['theme_sentiment'].to_csv(theme_sentiment_path, index=False)
        logger.info(f"Exported theme sentiment to {theme_sentiment_path}")
    
    # Export topic assignments
    if 'topic_df' in analysis_results:
        topic_path = os.path.join(exports_dir, "topic_assignments.csv")
        analysis_results['topic_df'][['url', 'title', 'theme_id', 'primary_topic', 'topic_confidence']].to_csv(topic_path, index=False)
        logger.info(f"Exported topic assignments to {topic_path}")
    
    logger.info(f"Generated all CSV exports in {exports_dir}")
    return exports_dir
