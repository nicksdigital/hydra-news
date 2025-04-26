#!/usr/bin/env python3
"""
GDELT Visualizer

This module provides functions for creating visualizations of GDELT news data analysis.
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap
import logging

# Set up logging
logger = logging.getLogger(__name__)

def setup_visualization_style():
    """Set up the visualization style"""
    # Set the style
    sns.set(style="whitegrid")
    
    # Set color palette
    sns.set_palette("viridis")
    
    # Set font scale
    sns.set_context("notebook", font_scale=1.2)
    
    # Set figure size
    plt.rcParams["figure.figsize"] = (12, 8)
    
    logger.info("Visualization style set up")

def create_theme_distribution_plot(theme_counts, output_dir, top_n=20):
    """
    Create a bar plot of theme distribution
    
    Args:
        theme_counts: DataFrame with theme counts
        output_dir: Directory to save the plot
        top_n: Number of top themes to include
    """
    logger.info(f"Creating theme distribution plot for top {top_n} themes")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Create the plot
    plt.figure(figsize=(12, 8))
    sns.barplot(x='count', y='theme_id', data=theme_counts.head(top_n), palette='viridis')
    plt.title(f'Top {top_n} Themes by Article Count')
    plt.xlabel('Number of Articles')
    plt.ylabel('Theme')
    plt.tight_layout()
    
    # Save the plot
    output_path = os.path.join(output_dir, 'theme_distribution.png')
    plt.savefig(output_path)
    plt.close()
    
    logger.info(f"Saved theme distribution plot to {output_path}")

def create_time_pattern_plots(date_counts, hour_counts, day_counts, output_dir):
    """
    Create plots of time patterns
    
    Args:
        date_counts: Series with article counts by date
        hour_counts: Series with article counts by hour
        day_counts: Series with article counts by day of week
        output_dir: Directory to save the plots
    """
    logger.info("Creating time pattern plots")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Articles by date
    plt.figure(figsize=(12, 6))
    date_counts.plot(kind='bar', color='skyblue')
    plt.title('Articles by Date')
    plt.xlabel('Date')
    plt.ylabel('Number of Articles')
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Save the plot
    date_path = os.path.join(output_dir, 'articles_by_date.png')
    plt.savefig(date_path)
    plt.close()
    
    # 2. Articles by hour of day
    plt.figure(figsize=(12, 6))
    hour_counts.plot(kind='bar', color='lightgreen')
    plt.title('Articles by Hour of Day')
    plt.xlabel('Hour')
    plt.ylabel('Number of Articles')
    plt.xticks(rotation=0)
    plt.tight_layout()
    
    # Save the plot
    hour_path = os.path.join(output_dir, 'articles_by_hour.png')
    plt.savefig(hour_path)
    plt.close()
    
    # 3. Articles by day of week
    plt.figure(figsize=(12, 6))
    day_counts.plot(kind='bar', color='salmon')
    plt.title('Articles by Day of Week')
    plt.xlabel('Day of Week')
    plt.ylabel('Number of Articles')
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Save the plot
    day_path = os.path.join(output_dir, 'articles_by_day.png')
    plt.savefig(day_path)
    plt.close()
    
    logger.info(f"Saved time pattern plots to {output_dir}")

def create_source_distribution_plots(domain_counts, tld_counts, language_counts, country_counts, output_dir):
    """
    Create plots of source distributions
    
    Args:
        domain_counts: Series with domain counts
        tld_counts: Series with TLD counts
        language_counts: Series with language counts
        country_counts: Series with country counts
        output_dir: Directory to save the plots
    """
    logger.info("Creating source distribution plots")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Top domains
    plt.figure(figsize=(12, 8))
    sns.barplot(x=domain_counts.values, y=domain_counts.index, palette='Blues_d')
    plt.title('Top Domains')
    plt.xlabel('Number of Articles')
    plt.ylabel('Domain')
    plt.tight_layout()
    
    # Save the plot
    domain_path = os.path.join(output_dir, 'top_domains.png')
    plt.savefig(domain_path)
    plt.close()
    
    # 2. Top TLDs
    plt.figure(figsize=(10, 6))
    sns.barplot(x=tld_counts.values, y=tld_counts.index, palette='Greens_d')
    plt.title('Top Top-Level Domains')
    plt.xlabel('Number of Articles')
    plt.ylabel('TLD')
    plt.tight_layout()
    
    # Save the plot
    tld_path = os.path.join(output_dir, 'top_tlds.png')
    plt.savefig(tld_path)
    plt.close()
    
    # 3. Language distribution
    plt.figure(figsize=(10, 6))
    sns.barplot(x=language_counts.values, y=language_counts.index, palette='Reds_d')
    plt.title('Top Languages')
    plt.xlabel('Number of Articles')
    plt.ylabel('Language')
    plt.tight_layout()
    
    # Save the plot
    language_path = os.path.join(output_dir, 'language_distribution.png')
    plt.savefig(language_path)
    plt.close()
    
    # 4. Country distribution
    plt.figure(figsize=(10, 8))
    sns.barplot(x=country_counts.values, y=country_counts.index, palette='Purples_d')
    plt.title('Top Source Countries')
    plt.xlabel('Number of Articles')
    plt.ylabel('Country')
    plt.tight_layout()
    
    # Save the plot
    country_path = os.path.join(output_dir, 'country_distribution.png')
    plt.savefig(country_path)
    plt.close()
    
    logger.info(f"Saved source distribution plots to {output_dir}")

def create_theme_correlation_heatmap(theme_corr, output_dir):
    """
    Create a heatmap of theme correlations
    
    Args:
        theme_corr: Correlation matrix of themes
        output_dir: Directory to save the plot
    """
    logger.info("Creating theme correlation heatmap")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Create the plot
    plt.figure(figsize=(12, 10))
    sns.heatmap(theme_corr, annot=True, cmap='coolwarm', vmin=-1, vmax=1)
    plt.title('Theme Correlation Matrix')
    plt.tight_layout()
    
    # Save the plot
    output_path = os.path.join(output_dir, 'theme_correlation.png')
    plt.savefig(output_path)
    plt.close()
    
    logger.info(f"Saved theme correlation heatmap to {output_path}")

def create_sentiment_distribution_plot(sentiment_df, output_dir):
    """
    Create plots of sentiment distribution
    
    Args:
        sentiment_df: DataFrame with sentiment scores
        output_dir: Directory to save the plots
    """
    logger.info("Creating sentiment distribution plots")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Filter out rows with NaN sentiment
    filtered_df = sentiment_df[sentiment_df['sentiment_polarity'].notna()]
    
    if len(filtered_df) == 0:
        logger.warning("No sentiment data available for plotting")
        return
    
    # 1. Sentiment polarity distribution
    plt.figure(figsize=(10, 6))
    sns.histplot(filtered_df['sentiment_polarity'], kde=True, bins=20)
    plt.title('Distribution of Sentiment Polarity')
    plt.xlabel('Polarity (-1 = Negative, 1 = Positive)')
    plt.ylabel('Count')
    plt.axvline(x=0, color='red', linestyle='--')
    plt.tight_layout()
    
    # Save the plot
    polarity_path = os.path.join(output_dir, 'sentiment_polarity.png')
    plt.savefig(polarity_path)
    plt.close()
    
    # 2. Sentiment subjectivity distribution
    plt.figure(figsize=(10, 6))
    sns.histplot(filtered_df['sentiment_subjectivity'], kde=True, bins=20)
    plt.title('Distribution of Sentiment Subjectivity')
    plt.xlabel('Subjectivity (0 = Objective, 1 = Subjective)')
    plt.ylabel('Count')
    plt.tight_layout()
    
    # Save the plot
    subjectivity_path = os.path.join(output_dir, 'sentiment_subjectivity.png')
    plt.savefig(subjectivity_path)
    plt.close()
    
    # 3. Sentiment by theme (top 10 themes)
    top_themes = filtered_df['theme_id'].value_counts().head(10).index
    theme_sentiment = filtered_df[filtered_df['theme_id'].isin(top_themes)]
    
    plt.figure(figsize=(12, 8))
    sns.boxplot(x='theme_id', y='sentiment_polarity', data=theme_sentiment)
    plt.title('Sentiment Polarity by Theme')
    plt.xlabel('Theme')
    plt.ylabel('Polarity (-1 = Negative, 1 = Positive)')
    plt.axhline(y=0, color='red', linestyle='--')
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Save the plot
    theme_sentiment_path = os.path.join(output_dir, 'sentiment_by_theme.png')
    plt.savefig(theme_sentiment_path)
    plt.close()
    
    logger.info(f"Saved sentiment distribution plots to {output_dir}")

def create_topic_word_cloud(topic_words, output_dir):
    """
    Create word clouds for topics
    
    Args:
        topic_words: List of lists of top words for each topic
        output_dir: Directory to save the plots
    """
    logger.info("Creating topic word clouds")
    
    try:
        from wordcloud import WordCloud
    except ImportError:
        logger.warning("wordcloud package not available. Skipping word cloud generation.")
        return
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Create word cloud for each topic
    for topic_idx, words in enumerate(topic_words):
        # Create word frequency dictionary
        word_freq = {word: len(topic_words) - i for i, word in enumerate(words)}
        
        # Create word cloud
        wordcloud = WordCloud(
            width=800,
            height=400,
            background_color='white',
            max_words=100
        ).generate_from_frequencies(word_freq)
        
        # Create the plot
        plt.figure(figsize=(10, 6))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        plt.title(f'Topic {topic_idx + 1}')
        plt.tight_layout()
        
        # Save the plot
        output_path = os.path.join(output_dir, f'topic_{topic_idx + 1}_wordcloud.png')
        plt.savefig(output_path)
        plt.close()
    
    logger.info(f"Saved topic word clouds to {output_dir}")

def create_time_series_plot(time_series, output_dir):
    """
    Create a time series plot
    
    Args:
        time_series: DataFrame with time series data
        output_dir: Directory to save the plot
    """
    logger.info("Creating time series plot")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Create the plot
    plt.figure(figsize=(14, 8))
    
    # Plot the raw counts
    plt.plot(time_series.index, time_series['count'], label='Articles', color='skyblue', alpha=0.7)
    
    # Plot the moving averages
    if 'ma_3' in time_series.columns:
        plt.plot(time_series.index, time_series['ma_3'], label='3-day MA', color='red', linewidth=2)
    
    if 'ma_7' in time_series.columns:
        plt.plot(time_series.index, time_series['ma_7'], label='7-day MA', color='green', linewidth=2)
    
    plt.title('Article Count Time Series')
    plt.xlabel('Date')
    plt.ylabel('Number of Articles')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    
    # Save the plot
    output_path = os.path.join(output_dir, 'time_series.png')
    plt.savefig(output_path)
    plt.close()
    
    logger.info(f"Saved time series plot to {output_path}")

def create_all_visualizations(analysis_results, output_dir):
    """
    Create all visualizations
    
    Args:
        analysis_results: Dictionary with analysis results
        output_dir: Directory to save the visualizations
    """
    logger.info("Creating all visualizations")
    
    # Set up visualization style
    setup_visualization_style()
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Create theme distribution plot
    if 'theme_counts' in analysis_results:
        create_theme_distribution_plot(
            analysis_results['theme_counts'],
            output_dir
        )
    
    # Create time pattern plots
    if all(k in analysis_results for k in ['date_counts', 'hour_counts', 'day_counts']):
        create_time_pattern_plots(
            analysis_results['date_counts'],
            analysis_results['hour_counts'],
            analysis_results['day_counts'],
            output_dir
        )
    
    # Create source distribution plots
    if all(k in analysis_results for k in ['domain_counts', 'tld_counts', 'language_counts', 'country_counts']):
        create_source_distribution_plots(
            analysis_results['domain_counts'],
            analysis_results['tld_counts'],
            analysis_results['language_counts'],
            analysis_results['country_counts'],
            output_dir
        )
    
    # Create theme correlation heatmap
    if 'theme_corr' in analysis_results:
        create_theme_correlation_heatmap(
            analysis_results['theme_corr'],
            output_dir
        )
    
    # Create sentiment distribution plot
    if 'sentiment_df' in analysis_results:
        create_sentiment_distribution_plot(
            analysis_results['sentiment_df'],
            output_dir
        )
    
    # Create topic word cloud
    if 'topic_words' in analysis_results:
        create_topic_word_cloud(
            analysis_results['topic_words'],
            output_dir
        )
    
    # Create time series plot
    if 'time_series' in analysis_results:
        create_time_series_plot(
            analysis_results['time_series'],
            output_dir
        )
    
    logger.info(f"Created all visualizations in {output_dir}")
