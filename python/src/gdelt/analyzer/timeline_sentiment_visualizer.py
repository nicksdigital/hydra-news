#!/usr/bin/env python3
"""
GDELT Timeline Sentiment Visualizer

This module provides functions for visualizing sentiment in entity timelines.
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
from datetime import datetime, timedelta
import logging
import json
from collections import defaultdict

# Set up logging
logger = logging.getLogger(__name__)

class TimelineSentimentVisualizer:
    """Class for visualizing sentiment in entity timelines"""
    
    def __init__(self):
        """Initialize the timeline sentiment visualizer"""
        # Set up visualization style
        plt.style.use('seaborn-v0_8-whitegrid')
        sns.set_palette("viridis")
    
    def create_sentiment_visualization(self, entity_text, articles_df, daily_sentiment, 
                                     output_path, event_data=None):
        """
        Create a visualization of sentiment during an event
        
        Args:
            entity_text: Text of the entity
            articles_df: DataFrame containing articles
            daily_sentiment: Series with daily sentiment values
            output_path: Path to save the visualization
            event_data: Optional event data dictionary
            
        Returns:
            Path to the saved visualization
        """
        # Set up the figure
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), gridspec_kw={'height_ratios': [3, 1]})
        
        # Plot 1: Sentiment scores for individual articles
        scatter = ax1.scatter(
            articles_df['seendate'], 
            articles_df['sentiment_score'],
            c=articles_df['sentiment_score'].apply(
                lambda x: 'green' if x > 0.1 else ('red' if x < -0.1 else 'gray')
            ),
            alpha=0.7,
            s=100
        )
        
        # Add a horizontal line at y=0
        ax1.axhline(y=0, color='black', linestyle='-', alpha=0.3)
        
        # Add horizontal lines for sentiment thresholds
        ax1.axhline(y=0.1, color='green', linestyle='--', alpha=0.3)
        ax1.axhline(y=-0.1, color='red', linestyle='--', alpha=0.3)
        
        # Set title and labels
        ax1.set_title(f"Sentiment Analysis for '{entity_text}'", fontsize=16)
        ax1.set_xlabel('Date', fontsize=12)
        ax1.set_ylabel('Sentiment Score', fontsize=12)
        
        # Set y-axis limits
        ax1.set_ylim(-1.1, 1.1)
        
        # Format x-axis
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax1.xaxis.set_major_locator(mdates.DayLocator(interval=1))
        plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        # Add grid
        ax1.grid(True, linestyle='--', alpha=0.3)
        
        # Plot 2: Daily average sentiment
        daily_sentiment.plot(ax=ax2, marker='o', linestyle='-', color='blue')
        
        # Add a horizontal line at y=0
        ax2.axhline(y=0, color='black', linestyle='-', alpha=0.3)
        
        # Set title and labels
        ax2.set_title('Daily Average Sentiment', fontsize=14)
        ax2.set_xlabel('Date', fontsize=12)
        ax2.set_ylabel('Avg. Sentiment', fontsize=12)
        
        # Set y-axis limits
        ax2.set_ylim(-1.1, 1.1)
        
        # Format x-axis
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax2.xaxis.set_major_locator(mdates.DayLocator(interval=1))
        plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        # Add grid
        ax2.grid(True, linestyle='--', alpha=0.3)
        
        # Add event information if provided
        if event_data and 'peak_date' in event_data:
            peak_date = datetime.strptime(event_data['peak_date'], '%Y-%m-%d')
            ax1.axvline(x=peak_date, color='purple', linestyle='-', alpha=0.5, label='Peak Date')
            ax2.axvline(x=peak_date, color='purple', linestyle='-', alpha=0.5)
        
        # Add legend
        ax1.legend(['Neutral', 'Positive Threshold', 'Negative Threshold', 'Peak Date'])
        
        # Add sentiment statistics
        sentiment_stats = f"""
        Overall Sentiment: {articles_df['sentiment_score'].mean():.2f}
        Positive Articles: {(articles_df['sentiment_score'] > 0.1).sum()} ({(articles_df['sentiment_score'] > 0.1).sum() / len(articles_df) * 100:.1f}%)
        Neutral Articles: {((articles_df['sentiment_score'] >= -0.1) & (articles_df['sentiment_score'] <= 0.1)).sum()} ({((articles_df['sentiment_score'] >= -0.1) & (articles_df['sentiment_score'] <= 0.1)).sum() / len(articles_df) * 100:.1f}%)
        Negative Articles: {(articles_df['sentiment_score'] < -0.1).sum()} ({(articles_df['sentiment_score'] < -0.1).sum() / len(articles_df) * 100:.1f}%)
        """
        
        plt.figtext(0.15, 0.01, sentiment_stats, fontsize=10, 
                   bbox=dict(facecolor='white', alpha=0.8))
        
        # Adjust layout
        plt.tight_layout()
        plt.subplots_adjust(bottom=0.15)
        
        # Save the plot
        plt.savefig(output_path)
        plt.close()
        
        logger.info(f"Created sentiment visualization for '{entity_text}' at {output_path}")
        
        return output_path
    
    def create_sentiment_timeline_visualization(self, entity_text, daily_sentiment, 
                                              rolling_sentiment, output_path):
        """
        Create a visualization of sentiment over time
        
        Args:
            entity_text: Text of the entity
            daily_sentiment: Series with daily sentiment values
            rolling_sentiment: Series with rolling average sentiment values
            output_path: Path to save the visualization
            
        Returns:
            Path to the saved visualization
        """
        # Set up the figure
        plt.figure(figsize=(14, 8))
        
        # Plot daily sentiment
        plt.plot(daily_sentiment.index, daily_sentiment.values, 'o-', 
                alpha=0.5, label='Daily Sentiment')
        
        # Plot rolling average
        plt.plot(rolling_sentiment.index, rolling_sentiment.values, 'r-', 
                linewidth=2, label='7-day Rolling Average')
        
        # Add a horizontal line at y=0
        plt.axhline(y=0, color='black', linestyle='-', alpha=0.3)
        
        # Add horizontal lines for sentiment thresholds
        plt.axhline(y=0.1, color='green', linestyle='--', alpha=0.3, label='Positive Threshold')
        plt.axhline(y=-0.1, color='red', linestyle='--', alpha=0.3, label='Negative Threshold')
        
        # Set title and labels
        plt.title(f"Sentiment Timeline for '{entity_text}'", fontsize=16)
        plt.xlabel('Date', fontsize=12)
        plt.ylabel('Sentiment Score', fontsize=12)
        
        # Set y-axis limits
        plt.ylim(-1.1, 1.1)
        
        # Format x-axis
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        plt.gca().xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))
        plt.xticks(rotation=45, ha='right')
        
        # Add grid
        plt.grid(True, linestyle='--', alpha=0.3)
        
        # Add legend
        plt.legend()
        
        # Add sentiment statistics
        sentiment_stats = f"""
        Overall Sentiment: {daily_sentiment.mean():.2f}
        Positive Days: {(daily_sentiment > 0.1).sum()} ({(daily_sentiment > 0.1).sum() / len(daily_sentiment) * 100:.1f}%)
        Neutral Days: {((daily_sentiment >= -0.1) & (daily_sentiment <= 0.1)).sum()} ({((daily_sentiment >= -0.1) & (daily_sentiment <= 0.1)).sum() / len(daily_sentiment) * 100:.1f}%)
        Negative Days: {(daily_sentiment < -0.1).sum()} ({(daily_sentiment < -0.1).sum() / len(daily_sentiment) * 100:.1f}%)
        """
        
        plt.figtext(0.15, 0.01, sentiment_stats, fontsize=10, 
                   bbox=dict(facecolor='white', alpha=0.8))
        
        # Adjust layout
        plt.tight_layout()
        plt.subplots_adjust(bottom=0.15)
        
        # Save the plot
        plt.savefig(output_path)
        plt.close()
        
        logger.info(f"Created sentiment timeline visualization for '{entity_text}' at {output_path}")
        
        return output_path
    
    def create_entity_sentiment_comparison(self, entity_list, sentiment_data, output_dir="timelines"):
        """
        Create a comparison visualization of sentiment for multiple entities
        
        Args:
            entity_list: List of entities to compare
            sentiment_data: Dictionary with sentiment data for each entity
            output_dir: Directory to save the visualization
            
        Returns:
            Path to the saved visualization
        """
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Set up the figure
        plt.figure(figsize=(14, 10))
        
        # Set color palette
        colors = sns.color_palette("husl", len(entity_list))
        
        # Plot rolling sentiment for each entity
        for i, entity in enumerate(entity_list):
            if entity not in sentiment_data:
                logger.warning(f"No sentiment data for entity '{entity}'")
                continue
            
            # Get rolling sentiment
            if 'rolling_sentiment' in sentiment_data[entity]:
                rolling_sentiment = sentiment_data[entity]['rolling_sentiment']
                
                # Convert string dates to datetime
                dates = [datetime.strptime(d, '%Y-%m-%d').date() for d in rolling_sentiment.keys()]
                values = list(rolling_sentiment.values())
                
                # Plot the sentiment
                plt.plot(dates, values, marker='', linestyle='-', 
                        color=colors[i], label=entity, alpha=0.7, linewidth=2)
        
        # Add a horizontal line at y=0
        plt.axhline(y=0, color='black', linestyle='-', alpha=0.3)
        
        # Add horizontal lines for sentiment thresholds
        plt.axhline(y=0.1, color='green', linestyle='--', alpha=0.3, label='Positive Threshold')
        plt.axhline(y=-0.1, color='red', linestyle='--', alpha=0.3, label='Negative Threshold')
        
        # Set title and labels
        plt.title(f"Sentiment Comparison for Multiple Entities", fontsize=16)
        plt.xlabel('Date', fontsize=12)
        plt.ylabel('Sentiment Score', fontsize=12)
        
        # Set y-axis limits
        plt.ylim(-1.1, 1.1)
        
        # Format x-axis
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        plt.gca().xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))
        plt.xticks(rotation=45, ha='right')
        
        # Add grid
        plt.grid(True, linestyle='--', alpha=0.3)
        
        # Add legend
        plt.legend()
        
        # Adjust layout
        plt.tight_layout()
        
        # Save the plot
        output_path = os.path.join(
            output_dir, 
            f"entity_sentiment_comparison_{'_'.join([e.replace(' ', '_') for e in entity_list[:3]])}.png"
        )
        plt.savefig(output_path)
        plt.close()
        
        logger.info(f"Created sentiment comparison visualization at {output_path}")
        
        return output_path
    
    def create_sentiment_heatmap(self, entity_list, sentiment_data, output_dir="timelines"):
        """
        Create a heatmap of sentiment for multiple entities over time
        
        Args:
            entity_list: List of entities to include
            sentiment_data: Dictionary with sentiment data for each entity
            output_dir: Directory to save the visualization
            
        Returns:
            Path to the saved visualization
        """
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Collect data for heatmap
        heatmap_data = {}
        all_dates = set()
        
        for entity in entity_list:
            if entity not in sentiment_data:
                logger.warning(f"No sentiment data for entity '{entity}'")
                continue
            
            # Get daily sentiment
            if 'daily_sentiment' in sentiment_data[entity]:
                daily_sentiment = sentiment_data[entity]['daily_sentiment']
                
                # Add to heatmap data
                heatmap_data[entity] = daily_sentiment
                
                # Collect all dates
                all_dates.update(daily_sentiment.keys())
        
        if not heatmap_data:
            logger.warning("No sentiment data available for heatmap")
            return None
        
        # Convert to DataFrame
        all_dates = sorted(all_dates)
        heatmap_df = pd.DataFrame(index=all_dates, columns=list(heatmap_data.keys()))
        
        for entity, sentiment in heatmap_data.items():
            for date, value in sentiment.items():
                heatmap_df.loc[date, entity] = value
        
        # Fill missing values with NaN
        heatmap_df = heatmap_df.astype(float)
        
        # Set up the figure
        plt.figure(figsize=(14, 10))
        
        # Create heatmap
        sns.heatmap(
            heatmap_df.T,  # Transpose to have entities as rows
            cmap='RdBu_r',  # Red-Blue colormap (reversed)
            center=0,  # Center colormap at 0
            vmin=-1,  # Minimum value
            vmax=1,  # Maximum value
            cbar_kws={'label': 'Sentiment Score'},
            linewidths=0.5,
            linecolor='gray'
        )
        
        # Set title and labels
        plt.title(f"Sentiment Heatmap for Multiple Entities", fontsize=16)
        plt.xlabel('Date', fontsize=12)
        plt.ylabel('Entity', fontsize=12)
        
        # Format x-axis
        plt.xticks(rotation=45, ha='right')
        
        # Adjust layout
        plt.tight_layout()
        
        # Save the plot
        output_path = os.path.join(
            output_dir, 
            f"entity_sentiment_heatmap_{'_'.join([e.replace(' ', '_') for e in entity_list[:3]])}.png"
        )
        plt.savefig(output_path)
        plt.close()
        
        logger.info(f"Created sentiment heatmap at {output_path}")
        
        return output_path
    
    def create_sentiment_distribution(self, entity_list, sentiment_data, output_dir="timelines"):
        """
        Create a distribution visualization of sentiment for multiple entities
        
        Args:
            entity_list: List of entities to compare
            sentiment_data: Dictionary with sentiment data for each entity
            output_dir: Directory to save the visualization
            
        Returns:
            Path to the saved visualization
        """
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Set up the figure
        plt.figure(figsize=(14, 8))
        
        # Collect sentiment values for each entity
        entity_sentiments = {}
        
        for entity in entity_list:
            if entity not in sentiment_data:
                logger.warning(f"No sentiment data for entity '{entity}'")
                continue
            
            # Get daily sentiment
            if 'daily_sentiment' in sentiment_data[entity]:
                daily_sentiment = sentiment_data[entity]['daily_sentiment']
                
                # Add to entity sentiments
                entity_sentiments[entity] = list(daily_sentiment.values())
        
        if not entity_sentiments:
            logger.warning("No sentiment data available for distribution")
            return None
        
        # Create violin plot
        sns.violinplot(
            data=[values for values in entity_sentiments.values()],
            palette="husl",
            inner="quartile"
        )
        
        # Set title and labels
        plt.title(f"Sentiment Distribution Comparison", fontsize=16)
        plt.xlabel('Entity', fontsize=12)
        plt.ylabel('Sentiment Score', fontsize=12)
        
        # Set y-axis limits
        plt.ylim(-1.1, 1.1)
        
        # Add horizontal lines for sentiment thresholds
        plt.axhline(y=0, color='black', linestyle='-', alpha=0.3)
        plt.axhline(y=0.1, color='green', linestyle='--', alpha=0.3)
        plt.axhline(y=-0.1, color='red', linestyle='--', alpha=0.3)
        
        # Set x-tick labels
        plt.xticks(range(len(entity_sentiments)), entity_sentiments.keys())
        
        # Add grid
        plt.grid(True, axis='y', linestyle='--', alpha=0.3)
        
        # Adjust layout
        plt.tight_layout()
        
        # Save the plot
        output_path = os.path.join(
            output_dir, 
            f"entity_sentiment_distribution_{'_'.join([e.replace(' ', '_') for e in entity_list[:3]])}.png"
        )
        plt.savefig(output_path)
        plt.close()
        
        logger.info(f"Created sentiment distribution visualization at {output_path}")
        
        return output_path
