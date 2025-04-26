#!/usr/bin/env python3
"""
GDELT Event Sentiment Analyzer

This module provides functions for analyzing sentiment towards entities during specific events.
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
import requests
from bs4 import BeautifulSoup
import time
import random

# Set up logging
logger = logging.getLogger(__name__)

# Try to import transformers for sentiment analysis
try:
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    import torch
    TRANSFORMERS_AVAILABLE = True
    logger.info("Transformers library available for sentiment analysis")
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logger.warning("Transformers library not available. Using basic sentiment analysis.")

# Try to import TextBlob as fallback
try:
    from textblob import TextBlob
    TEXTBLOB_AVAILABLE = True
except ImportError:
    TEXTBLOB_AVAILABLE = False
    logger.warning("TextBlob not available. Using basic sentiment analysis.")

class EventSentimentAnalyzer:
    """Class for analyzing sentiment towards entities during events"""

    def __init__(self, db_manager=None):
        """
        Initialize the event sentiment analyzer

        Args:
            db_manager: DatabaseManager instance for accessing stored data
        """
        self.db_manager = db_manager
        self.sentiment_model = self._load_sentiment_model()
        self.sentiment_lexicon = self._load_sentiment_lexicon()

    def _load_sentiment_model(self):
        """Load the Hugging Face sentiment analysis model"""
        if TRANSFORMERS_AVAILABLE:
            try:
                # Use the multilingual sentiment analysis model
                model_name = "tabularisai/multilingual-sentiment-analysis"
                tokenizer = AutoTokenizer.from_pretrained(model_name)
                model = AutoModelForSequenceClassification.from_pretrained(model_name)

                # Create a model wrapper
                sentiment_model = {
                    'tokenizer': tokenizer,
                    'model': model,
                    'sentiment_map': {0: "Very Negative", 1: "Negative", 2: "Neutral", 3: "Positive", 4: "Very Positive"}
                }

                logger.info(f"Loaded sentiment analysis model: {model_name}")
                return sentiment_model
            except Exception as e:
                logger.error(f"Error loading sentiment analysis model: {e}")
                return None
        return None

    def _load_sentiment_lexicon(self):
        """Load a basic sentiment lexicon for fallback sentiment analysis"""
        # Simple sentiment lexicon with positive and negative words
        positive_words = [
            'good', 'great', 'excellent', 'positive', 'success', 'successful', 'win', 'winning',
            'best', 'better', 'improve', 'improved', 'improvement', 'support', 'supported',
            'agree', 'agreement', 'cooperation', 'collaborative', 'peace', 'peaceful',
            'progress', 'progressive', 'advance', 'advancement', 'benefit', 'beneficial',
            'advantage', 'advantageous', 'opportunity', 'promising', 'hope', 'hopeful'
        ]

        negative_words = [
            'bad', 'worst', 'terrible', 'negative', 'fail', 'failure', 'lose', 'losing',
            'lost', 'poor', 'poorly', 'worsen', 'worsened', 'decline', 'declined',
            'disagree', 'disagreement', 'conflict', 'war', 'hostile', 'hostility',
            'attack', 'attacking', 'attacked', 'threat', 'threatening', 'problem',
            'crisis', 'critical', 'danger', 'dangerous', 'risk', 'risky', 'fear',
            'afraid', 'worry', 'concerned', 'concern', 'issue', 'trouble', 'difficult'
        ]

        # Create lexicon dictionary with sentiment scores
        lexicon = {}
        for word in positive_words:
            lexicon[word] = 0.5

        for word in negative_words:
            lexicon[word] = -0.5

        return lexicon

    def analyze_event_sentiment(self, entity_text, event_data, output_dir="timelines"):
        """
        Analyze sentiment towards an entity during a specific event

        Args:
            entity_text: Text of the entity
            event_data: Event data dictionary
            output_dir: Directory to save the output

        Returns:
            Dictionary with sentiment analysis results
        """
        logger.info(f"Analyzing sentiment for entity '{entity_text}' during event")

        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

        # Get articles for the event
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

            # Get start and end dates for the event
            start_date = event_data.get('start_date')
            end_date = event_data.get('end_date')

            if not start_date or not end_date:
                logger.warning("Event data missing start_date or end_date")
                return None

            # Get articles mentioning the entity during the event
            query = """
            SELECT a.id, a.url, a.title, a.seendate, a.language, a.domain,
                   a.sourcecountry, a.theme_id, a.theme_description, a.trust_score
            FROM articles a
            JOIN article_entities ae ON a.id = ae.article_id
            WHERE ae.entity_id = ?
              AND a.seendate >= ?
              AND a.seendate <= ?
            ORDER BY a.seendate
            """

            articles_df = pd.read_sql_query(
                query,
                self.db_manager.conn,
                params=[entity_id, start_date, end_date]
            )

            if articles_df.empty:
                logger.warning(f"No articles found for entity '{entity_text}' during event")
                return None

            logger.info(f"Found {len(articles_df)} articles for entity '{entity_text}' during event")
        else:
            # If no database connection, use articles from event data
            if 'top_articles' in event_data:
                # Create DataFrame from top articles
                articles_df = pd.DataFrame(event_data['top_articles'])

                # Convert date strings to datetime
                articles_df['seendate'] = pd.to_datetime(articles_df['date'])

                logger.info(f"Using {len(articles_df)} top articles from event data")
            else:
                logger.warning("No articles available for sentiment analysis")
                return None

        # Analyze sentiment for each article
        articles_df['sentiment_score'] = articles_df.apply(
            lambda row: self._analyze_sentiment(row['title'], row['url']), axis=1
        )

        # Calculate daily sentiment
        articles_df['date'] = pd.to_datetime(articles_df['seendate']).dt.date
        daily_sentiment = articles_df.groupby('date')['sentiment_score'].mean()

        # Calculate overall sentiment statistics
        sentiment_stats = {
            'mean': articles_df['sentiment_score'].mean(),
            'median': articles_df['sentiment_score'].median(),
            'min': articles_df['sentiment_score'].min(),
            'max': articles_df['sentiment_score'].max(),
            'std': articles_df['sentiment_score'].std(),
            'positive_count': (articles_df['sentiment_score'] > 0.1).sum(),
            'neutral_count': ((articles_df['sentiment_score'] >= -0.1) &
                             (articles_df['sentiment_score'] <= 0.1)).sum(),
            'negative_count': (articles_df['sentiment_score'] < -0.1).sum()
        }

        # Calculate sentiment by source
        source_sentiment = articles_df.groupby('domain')['sentiment_score'].mean().sort_values()

        # Create sentiment visualization
        sentiment_chart_path = os.path.join(
            output_dir,
            f"{entity_text.replace(' ', '_')}_event_sentiment.png"
        )
        self._create_sentiment_visualization(
            entity_text,
            articles_df,
            daily_sentiment,
            sentiment_chart_path,
            event_data
        )

        # Create sentiment results
        sentiment_results = {
            'entity': entity_text,
            'event_start_date': start_date,
            'event_end_date': end_date,
            'article_count': len(articles_df),
            'sentiment_stats': sentiment_stats,
            'daily_sentiment': {str(k): v for k, v in daily_sentiment.to_dict().items()},
            'source_sentiment': {k: v for k, v in source_sentiment.head(10).to_dict().items()},
            'sentiment_chart': sentiment_chart_path,
            'articles_with_sentiment': []
        }

        # Add articles with sentiment
        for _, row in articles_df.sort_values('seendate').iterrows():
            sentiment_results['articles_with_sentiment'].append({
                'title': row['title'],
                'url': row['url'],
                'date': row['seendate'].strftime('%Y-%m-%d') if hasattr(row['seendate'], 'strftime') else row['seendate'],
                'source': row['domain'],
                'sentiment_score': float(row['sentiment_score']),
                'sentiment_category': self._get_sentiment_category(row['sentiment_score'])
            })

        # Save sentiment results
        sentiment_json_path = os.path.join(
            output_dir,
            f"{entity_text.replace(' ', '_')}_event_sentiment.json"
        )
        with open(sentiment_json_path, 'w') as f:
            json.dump(sentiment_results, f, indent=2)

        logger.info(f"Saved sentiment analysis results to {sentiment_json_path}")

        return sentiment_results

    def analyze_entity_sentiment_over_time(self, entity_text, start_date=None, end_date=None,
                                         output_dir="timelines"):
        """
        Analyze sentiment towards an entity over time

        Args:
            entity_text: Text of the entity
            start_date: Start date for analysis (None for all data)
            end_date: End date for analysis (None for all data)
            output_dir: Directory to save the output

        Returns:
            Dictionary with sentiment analysis results
        """
        logger.info(f"Analyzing sentiment for entity '{entity_text}' over time")

        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

        # Get articles for the entity
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

        # Analyze sentiment for each article
        articles_df['sentiment_score'] = articles_df.apply(
            lambda row: self._analyze_sentiment(row['title'], row['url']), axis=1
        )

        # Convert seendate to datetime
        articles_df['seendate'] = pd.to_datetime(articles_df['seendate'])

        # Calculate daily sentiment
        articles_df['date'] = articles_df['seendate'].dt.date
        daily_sentiment = articles_df.groupby('date')['sentiment_score'].mean()

        # Calculate rolling average sentiment (7-day window)
        if len(daily_sentiment) >= 7:
            rolling_sentiment = daily_sentiment.rolling(window=7, min_periods=1).mean()
        else:
            rolling_sentiment = daily_sentiment

        # Calculate overall sentiment statistics
        sentiment_stats = {
            'mean': float(articles_df['sentiment_score'].mean()),
            'median': float(articles_df['sentiment_score'].median()),
            'min': float(articles_df['sentiment_score'].min()),
            'max': float(articles_df['sentiment_score'].max()),
            'std': float(articles_df['sentiment_score'].std()),
            'positive_count': int((articles_df['sentiment_score'] > 0.1).sum()),
            'neutral_count': int(((articles_df['sentiment_score'] >= -0.1) &
                             (articles_df['sentiment_score'] <= 0.1)).sum()),
            'negative_count': int((articles_df['sentiment_score'] < -0.1).sum())
        }

        # Calculate sentiment by source
        source_sentiment = articles_df.groupby('domain')['sentiment_score'].mean().sort_values()

        # Calculate sentiment by theme
        theme_sentiment = articles_df.groupby('theme_id')['sentiment_score'].mean().sort_values()

        # Create sentiment visualization
        sentiment_chart_path = os.path.join(
            output_dir,
            f"{entity_text.replace(' ', '_')}_sentiment_timeline.png"
        )
        self._create_sentiment_timeline_visualization(
            entity_text,
            daily_sentiment,
            rolling_sentiment,
            sentiment_chart_path
        )

        # Create sentiment results
        sentiment_results = {
            'entity': entity_text,
            'start_date': articles_df['seendate'].min().strftime('%Y-%m-%d'),
            'end_date': articles_df['seendate'].max().strftime('%Y-%m-%d'),
            'article_count': len(articles_df),
            'sentiment_stats': sentiment_stats,
            'daily_sentiment': {str(k): float(v) for k, v in daily_sentiment.to_dict().items()},
            'rolling_sentiment': {str(k): float(v) for k, v in rolling_sentiment.to_dict().items()},
            'source_sentiment': {str(k): float(v) for k, v in source_sentiment.head(10).to_dict().items()},
            'theme_sentiment': {str(k): float(v) for k, v in theme_sentiment.to_dict().items()},
            'sentiment_chart': sentiment_chart_path
        }

        # Save sentiment results
        sentiment_json_path = os.path.join(
            output_dir,
            f"{entity_text.replace(' ', '_')}_sentiment_timeline.json"
        )
        with open(sentiment_json_path, 'w') as f:
            json.dump(sentiment_results, f, indent=2)

        logger.info(f"Saved sentiment timeline results to {sentiment_json_path}")

        return sentiment_results

    def _fetch_article_content(self, url):
        """
        Fetch article content from URL

        Args:
            url: URL of the article

        Returns:
            Article content as text
        """
        if pd.isna(url) or url == '':
            return ''

        try:
            # Add a random delay to avoid being blocked
            time.sleep(random.uniform(1, 3))

            # Set headers to mimic a browser
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Cache-Control': 'max-age=0'
            }

            # Send request with timeout
            response = requests.get(url, headers=headers, timeout=10)

            # Check if request was successful
            if response.status_code == 200:
                # Parse HTML
                soup = BeautifulSoup(response.text, 'html.parser')

                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.extract()

                # Get text
                text = soup.get_text()

                # Clean text
                lines = (line.strip() for line in text.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                text = '\n'.join(chunk for chunk in chunks if chunk)

                return text
            else:
                logger.warning(f"Failed to fetch article content: {response.status_code}")
                return ''
        except Exception as e:
            logger.warning(f"Error fetching article content: {e}")
            return ''

    def _analyze_sentiment(self, text, url=None):
        """
        Analyze sentiment of a text

        Args:
            text: Text to analyze (article title)
            url: URL of the article (optional)

        Returns:
            Sentiment score (-1 to 1)
        """
        if pd.isna(text) or text == '':
            return 0.0

        # Try to fetch article content if URL is provided
        article_content = ''
        if url is not None and not pd.isna(url) and url != '':
            article_content = self._fetch_article_content(url)

        # If we have article content, analyze that instead of just the title
        if article_content:
            text_to_analyze = article_content
        else:
            text_to_analyze = text

        # Use Hugging Face model if available
        if self.sentiment_model is not None:
            try:
                # Truncate text to avoid model issues
                text_to_analyze = text_to_analyze[:512]

                # Get sentiment prediction using the model
                tokenizer = self.sentiment_model['tokenizer']
                model = self.sentiment_model['model']
                sentiment_map = self.sentiment_model['sentiment_map']

                # Tokenize and get model outputs
                inputs = tokenizer(text_to_analyze, return_tensors="pt", truncation=True, padding=True, max_length=512)
                with torch.no_grad():
                    outputs = model(**inputs)

                # Get probabilities and predicted sentiment
                probabilities = torch.nn.functional.softmax(outputs.logits, dim=-1)
                sentiment_idx = torch.argmax(probabilities, dim=-1).item()
                sentiment_label = sentiment_map[sentiment_idx]
                confidence = probabilities[0][sentiment_idx].item()

                # Convert to -1 to 1 scale
                if sentiment_label in ["Positive", "Very Positive"]:
                    return confidence if sentiment_label == "Positive" else confidence * 1.5
                elif sentiment_label in ["Negative", "Very Negative"]:
                    return -confidence if sentiment_label == "Negative" else -confidence * 1.5
                else:  # Neutral
                    return 0.0

            except Exception as e:
                logger.error(f"Error analyzing sentiment with model: {e}")
                # Fall back to TextBlob or lexicon-based approach

        # Use TextBlob if available
        if TEXTBLOB_AVAILABLE:
            try:
                blob = TextBlob(text_to_analyze)
                return blob.sentiment.polarity
            except Exception as e:
                logger.error(f"Error analyzing sentiment with TextBlob: {e}")
                # Fall back to lexicon-based approach

        # Lexicon-based approach
        text_to_analyze = text_to_analyze.lower()
        words = text_to_analyze.split()

        # Calculate sentiment score
        sentiment_score = 0.0
        matched_words = 0

        for word in words:
            # Clean word
            word = word.strip('.,!?;:()[]{}""\'')

            if word in self.sentiment_lexicon:
                sentiment_score += self.sentiment_lexicon[word]
                matched_words += 1

        # Normalize score
        if matched_words > 0:
            sentiment_score = sentiment_score / matched_words

        return sentiment_score

    def _get_sentiment_category(self, score):
        """Get sentiment category from score"""
        if score > 0.1:
            return 'positive'
        elif score < -0.1:
            return 'negative'
        else:
            return 'neutral'

    def _create_sentiment_visualization(self, entity_text, articles_df, daily_sentiment,
                                      output_path, event_data):
        """Create a visualization of sentiment during an event"""
        # Set up the figure
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), gridspec_kw={'height_ratios': [3, 1]})

        # Plot 1: Sentiment scores for individual articles
        ax1.scatter(
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
        ax1.set_title(f"Sentiment Analysis for '{entity_text}' during Event", fontsize=16)
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

        # Add event information
        if 'peak_date' in event_data:
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

    def _create_sentiment_timeline_visualization(self, entity_text, daily_sentiment,
                                               rolling_sentiment, output_path):
        """Create a visualization of sentiment over time"""
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

    # Create report content
    report = f"""# Sentiment Analysis Report for '{entity}' during Event

## Overview

- **Event Period**: {sentiment_results['event_start_date']} to {sentiment_results['event_end_date']}
- **Total Articles**: {sentiment_results['article_count']}
- **Overall Sentiment**: {sentiment_results['sentiment_stats']['mean']:.2f} (on a scale from -1 to 1)

## Sentiment Distribution

- **Positive Articles**: {sentiment_results['sentiment_stats']['positive_count']} ({sentiment_results['sentiment_stats']['positive_count'] / sentiment_results['article_count'] * 100:.1f}%)
- **Neutral Articles**: {sentiment_results['sentiment_stats']['neutral_count']} ({sentiment_results['sentiment_stats']['neutral_count'] / sentiment_results['article_count'] * 100:.1f}%)
- **Negative Articles**: {sentiment_results['sentiment_stats']['negative_count']} ({sentiment_results['sentiment_stats']['negative_count'] / sentiment_results['article_count'] * 100:.1f}%)

## Sentiment Visualization

![Sentiment Chart]({entity.replace(' ', '_')}_event_sentiment.png)

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

    # Add positive articles
    positive_articles = [a for a in sentiment_results['articles_with_sentiment']
                        if a['sentiment_category'] == 'positive']
    for article in positive_articles[:5]:  # Limit to top 5
        report += f"| {article['date']} | {article['source']} | [{article['title']}]({article['url']}) | {article['sentiment_score']:.2f} |\n"

    report += """
### Negative Articles

| Date | Source | Title | Sentiment |
|------|--------|-------|-----------|
"""

    # Add negative articles
    negative_articles = [a for a in sentiment_results['articles_with_sentiment']
                        if a['sentiment_category'] == 'negative']
    for article in negative_articles[:5]:  # Limit to top 5
        report += f"| {article['date']} | {article['source']} | [{article['title']}]({article['url']}) | {article['sentiment_score']:.2f} |\n"

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
