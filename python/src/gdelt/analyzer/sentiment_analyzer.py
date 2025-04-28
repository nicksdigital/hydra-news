#!/usr/bin/env python3
"""
Sentiment Analyzer for GDELT News Articles using Hugging Face transformers

This module provides a class for analyzing sentiment in news articles.
"""

import pandas as pd
import logging
import re
import numpy as np

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Try to import transformers
try:
    from transformers import pipeline, AutoModelForSequenceClassification, AutoTokenizer
    TRANSFORMERS_AVAILABLE = True
    logger.info("Transformers library is available")
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logger.warning("Transformers library not available. Falling back to simple sentiment analysis")

# Try to import NLTK as fallback
try:
    import nltk
    from nltk.sentiment.vader import SentimentIntensityAnalyzer
    NLTK_AVAILABLE = True

    # Try to import NLTK resources
    try:
        nltk.data.find('vader_lexicon')
    except LookupError:
        try:
            nltk.download('vader_lexicon')
        except Exception as e:
            logger.warning(f"Could not download NLTK resources: {e}")
            NLTK_AVAILABLE = False
except ImportError:
    NLTK_AVAILABLE = False
    logger.warning("NLTK not available. Using simple sentiment analysis")

class SentimentAnalyzer:
    """Class for analyzing sentiment in text"""

    def __init__(self, model_name="tabularisai/multilingual-sentiment-analysis"):
        """
        Initialize the sentiment analyzer

        Args:
            model_name: Name of the Hugging Face model to use
        """
        self.model_name = model_name
        self.sentiment_pipeline = None
        self.vader_analyzer = None

        # Try to load Hugging Face model
        if TRANSFORMERS_AVAILABLE:
            try:
                logger.info(f"Loading sentiment analysis model: {model_name}")
                self.sentiment_pipeline = pipeline(
                    "sentiment-analysis",
                    model=model_name,
                    tokenizer=model_name,
                    return_all_scores=True
                )
                logger.info("Sentiment analysis model loaded successfully")
                return
            except Exception as e:
                logger.error(f"Error loading sentiment analysis model: {e}")
                self.sentiment_pipeline = None

        # Fall back to NLTK VADER
        if NLTK_AVAILABLE:
            try:
                self.vader_analyzer = SentimentIntensityAnalyzer()
                logger.info("Initialized VADER sentiment analyzer as fallback")
            except Exception as e:
                logger.warning(f"Could not initialize VADER: {e}")
                self.vader_analyzer = None

    def analyze_text(self, text):
        """
        Analyze sentiment in text

        Args:
            text: Text to analyze

        Returns:
            Dictionary with sentiment scores
        """
        if not text or pd.isna(text):
            return {'compound': 0.0, 'pos': 0.0, 'neu': 0.0, 'neg': 0.0}

        # Try using Hugging Face transformers
        if self.sentiment_pipeline:
            try:
                # Truncate text if it's too long (most models have a limit of 512 tokens)
                if len(text) > 1000:
                    text = text[:1000]

                # Get sentiment scores
                results = self.sentiment_pipeline(text)[0]

                # Convert to dictionary and map labels
                scores = {}
                for score in results:
                    label = score['label'].lower()
                    # Map LABEL_X to sentiment labels
                    if label == 'label_0':
                        mapped_label = 'negative'
                    elif label == 'label_1':
                        mapped_label = 'neutral'
                    elif label == 'label_2':
                        mapped_label = 'positive'
                    elif 'positive' in label:
                        mapped_label = 'positive'
                    elif 'negative' in label:
                        mapped_label = 'negative'
                    elif 'neutral' in label:
                        mapped_label = 'neutral'
                    else:
                        # Default mapping based on label index
                        if label.startswith('label_'):
                            try:
                                index = int(label.split('_')[1])
                                if index == 0:
                                    mapped_label = 'negative'
                                elif index == 1:
                                    mapped_label = 'neutral'
                                else:
                                    mapped_label = 'positive'
                            except:
                                mapped_label = label
                        else:
                            mapped_label = label

                    scores[mapped_label] = score['score']

                # Ensure we have all required keys
                if 'positive' not in scores:
                    scores['positive'] = 0.0
                if 'negative' not in scores:
                    scores['negative'] = 0.0
                if 'neutral' not in scores:
                    scores['neutral'] = 0.0

                # Map to standard format
                compound = scores.get('positive', 0.0) - scores.get('negative', 0.0)
                return {
                    'compound': compound,
                    'pos': scores.get('positive', 0.0),
                    'neu': scores.get('neutral', 0.0),
                    'neg': scores.get('negative', 0.0)
                }
            except Exception as e:
                logger.error(f"Error analyzing sentiment with transformer: {e}")

        # Try using VADER
        if self.vader_analyzer:
            try:
                return self.vader_analyzer.polarity_scores(text)
            except Exception as e:
                logger.error(f"Error analyzing sentiment with VADER: {e}")

        # Fallback to simple sentiment analysis
        return self._simple_sentiment(text)

    def _simple_sentiment(self, text):
        """Simple sentiment analysis using keyword matching"""
        # Define positive and negative word lists
        positive_words = ['good', 'great', 'excellent', 'positive', 'success', 'happy', 'win', 'best', 'improve']
        negative_words = ['bad', 'terrible', 'negative', 'fail', 'poor', 'worst', 'problem', 'crisis', 'conflict']

        # Normalize text
        text = text.lower()

        # Count positive and negative words
        pos_count = sum(1 for word in positive_words if re.search(r'\b' + word + r'\b', text))
        neg_count = sum(1 for word in negative_words if re.search(r'\b' + word + r'\b', text))

        # Calculate sentiment scores
        total = pos_count + neg_count
        if total == 0:
            return {'compound': 0.0, 'pos': 0.0, 'neu': 1.0, 'neg': 0.0}

        pos = pos_count / (pos_count + neg_count)
        neg = neg_count / (pos_count + neg_count)
        compound = (pos_count - neg_count) / (pos_count + neg_count)

        return {'compound': compound, 'pos': pos, 'neu': 0.0, 'neg': neg}

    def analyze_dataframe(self, df):
        """
        Analyze sentiment in a DataFrame of articles

        Args:
            df: DataFrame containing articles with 'title' column

        Returns:
            DataFrame with sentiment scores added
        """
        logger.info("Analyzing sentiment in DataFrame")

        # Make a copy to avoid modifying the original
        result_df = df.copy()

        # Add sentiment columns if they don't exist
        if 'sentiment_polarity' not in result_df.columns:
            result_df['sentiment_polarity'] = 0.0

        if 'sentiment_positive' not in result_df.columns:
            result_df['sentiment_positive'] = 0.0

        if 'sentiment_negative' not in result_df.columns:
            result_df['sentiment_negative'] = 0.0

        # Analyze sentiment for each article
        for idx, row in result_df.iterrows():
            title = row.get('title', '')

            if not title or pd.isna(title):
                continue

            # Analyze sentiment
            sentiment = self.analyze_text(title)

            # Update DataFrame
            result_df.at[idx, 'sentiment_polarity'] = sentiment['compound']
            result_df.at[idx, 'sentiment_positive'] = sentiment['pos']
            result_df.at[idx, 'sentiment_negative'] = sentiment['neg']

        logger.info("Sentiment analysis complete")
        return result_df
