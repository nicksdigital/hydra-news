#!/usr/bin/env python3
"""
GDELT Text Analyzer

This module provides functions for analyzing text content in GDELT news data,
including sentiment analysis and topic modeling.
"""

import pandas as pd
import numpy as np
from collections import Counter
import re
import logging
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

# Set up logging
logger = logging.getLogger(__name__)

# Initialize NLTK resources
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
    
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')
    
try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet')

# Try to import optional dependencies
try:
    from textblob import TextBlob
    TEXTBLOB_AVAILABLE = True
except ImportError:
    TEXTBLOB_AVAILABLE = False
    logger.warning("TextBlob not available. Sentiment analysis will be limited.")

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.decomposition import LatentDirichletAllocation
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("scikit-learn not available. Topic modeling will be limited.")

def preprocess_text(text):
    """
    Preprocess text for analysis
    
    Args:
        text: Text to preprocess
        
    Returns:
        Preprocessed text
    """
    if pd.isna(text) or text == '':
        return ''
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove URLs
    text = re.sub(r'https?://\S+|www\.\S+', '', text)
    
    # Remove HTML tags
    text = re.sub(r'<.*?>', '', text)
    
    # Remove special characters and numbers
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\d+', '', text)
    
    # Tokenize
    tokens = word_tokenize(text)
    
    # Remove stopwords
    stop_words = set(stopwords.words('english'))
    tokens = [token for token in tokens if token not in stop_words]
    
    # Lemmatize
    lemmatizer = WordNetLemmatizer()
    tokens = [lemmatizer.lemmatize(token) for token in tokens]
    
    # Join tokens back into text
    preprocessed_text = ' '.join(tokens)
    
    return preprocessed_text

def analyze_sentiment(articles):
    """
    Analyze sentiment in article titles
    
    Args:
        articles: DataFrame containing articles
        
    Returns:
        DataFrame with sentiment scores
    """
    logger.info("Analyzing sentiment in article titles")
    
    # Check if TextBlob is available
    if not TEXTBLOB_AVAILABLE:
        logger.warning("TextBlob not available. Skipping sentiment analysis.")
        return None
    
    # Create a copy of the DataFrame
    sentiment_df = articles.copy()
    
    # Initialize sentiment columns
    sentiment_df['sentiment_polarity'] = np.nan
    sentiment_df['sentiment_subjectivity'] = np.nan
    
    # Analyze sentiment for each title
    for idx, row in sentiment_df.iterrows():
        title = row['title']
        
        if pd.isna(title) or title == '':
            continue
        
        try:
            # Analyze sentiment using TextBlob
            blob = TextBlob(title)
            
            # Get sentiment polarity (-1 to 1) and subjectivity (0 to 1)
            sentiment_df.at[idx, 'sentiment_polarity'] = blob.sentiment.polarity
            sentiment_df.at[idx, 'sentiment_subjectivity'] = blob.sentiment.subjectivity
        except Exception as e:
            logger.error(f"Error analyzing sentiment for title: {title}. Error: {e}")
    
    logger.info(f"Analyzed sentiment for {sentiment_df['sentiment_polarity'].notna().sum()} articles")
    return sentiment_df

def analyze_sentiment_by_theme(sentiment_df):
    """
    Analyze sentiment by theme
    
    Args:
        sentiment_df: DataFrame with sentiment scores
        
    Returns:
        DataFrame with sentiment statistics by theme
    """
    logger.info("Analyzing sentiment by theme")
    
    # Group by theme and calculate sentiment statistics
    theme_sentiment = sentiment_df.groupby('theme_id').agg({
        'sentiment_polarity': ['mean', 'std', 'min', 'max', 'count'],
        'sentiment_subjectivity': ['mean', 'std', 'min', 'max']
    })
    
    # Flatten the column names
    theme_sentiment.columns = [f"{col[0]}_{col[1]}" for col in theme_sentiment.columns]
    
    # Reset index
    theme_sentiment = theme_sentiment.reset_index()
    
    # Add theme description
    theme_sentiment['theme_description'] = theme_sentiment['theme_id'].map(
        lambda x: sentiment_df[sentiment_df['theme_id'] == x]['theme_description'].iloc[0]
        if not sentiment_df[sentiment_df['theme_id'] == x].empty else None
    )
    
    # Sort by average polarity
    theme_sentiment = theme_sentiment.sort_values('sentiment_polarity_mean', ascending=False)
    
    logger.info(f"Analyzed sentiment for {len(theme_sentiment)} themes")
    return theme_sentiment

def extract_keywords(articles, min_count=3, max_keywords=100):
    """
    Extract keywords from article titles
    
    Args:
        articles: DataFrame containing articles
        min_count: Minimum count for a keyword to be included
        max_keywords: Maximum number of keywords to return
        
    Returns:
        DataFrame with keyword counts
    """
    logger.info("Extracting keywords from article titles")
    
    # Combine all titles
    all_titles = ' '.join(articles['title'].fillna(''))
    
    # Preprocess text
    preprocessed_text = preprocess_text(all_titles)
    
    # Tokenize
    tokens = word_tokenize(preprocessed_text)
    
    # Count tokens
    token_counts = Counter(tokens)
    
    # Filter by minimum count
    filtered_counts = {token: count for token, count in token_counts.items() if count >= min_count}
    
    # Convert to DataFrame
    keywords_df = pd.DataFrame([
        {'keyword': token, 'count': count}
        for token, count in filtered_counts.items()
    ])
    
    # Sort by count
    if not keywords_df.empty:
        keywords_df = keywords_df.sort_values('count', ascending=False).head(max_keywords)
    
    logger.info(f"Extracted {len(keywords_df)} keywords")
    return keywords_df

def build_topic_model(articles, n_topics=10, n_top_words=10):
    """
    Build a topic model from article titles
    
    Args:
        articles: DataFrame containing articles
        n_topics: Number of topics to extract
        n_top_words: Number of top words per topic
        
    Returns:
        Tuple of (topic model, vectorizer, feature names, document-topic matrix)
    """
    logger.info(f"Building topic model with {n_topics} topics")
    
    # Check if scikit-learn is available
    if not SKLEARN_AVAILABLE:
        logger.warning("scikit-learn not available. Skipping topic modeling.")
        return None
    
    # Preprocess titles
    preprocessed_titles = articles['title'].fillna('').apply(preprocess_text)
    
    # Remove empty titles
    preprocessed_titles = preprocessed_titles[preprocessed_titles != '']
    
    if len(preprocessed_titles) == 0:
        logger.warning("No valid titles for topic modeling.")
        return None
    
    # Create TF-IDF vectorizer
    vectorizer = TfidfVectorizer(
        max_features=1000,
        min_df=5,
        max_df=0.9
    )
    
    # Transform titles to TF-IDF features
    tfidf_matrix = vectorizer.fit_transform(preprocessed_titles)
    
    # Get feature names
    feature_names = vectorizer.get_feature_names_out()
    
    # Build LDA model
    lda = LatentDirichletAllocation(
        n_components=n_topics,
        random_state=42,
        max_iter=10
    )
    
    # Fit the model
    doc_topic_matrix = lda.fit_transform(tfidf_matrix)
    
    logger.info(f"Built topic model with {n_topics} topics and {len(feature_names)} features")
    return lda, vectorizer, feature_names, doc_topic_matrix

def get_topic_words(lda_model, feature_names, n_top_words=10):
    """
    Get top words for each topic
    
    Args:
        lda_model: Trained LDA model
        feature_names: Feature names from vectorizer
        n_top_words: Number of top words per topic
        
    Returns:
        List of lists of top words for each topic
    """
    logger.info(f"Extracting top {n_top_words} words for each topic")
    
    topic_words = []
    for topic_idx, topic in enumerate(lda_model.components_):
        # Get indices of top words
        top_word_indices = topic.argsort()[:-n_top_words-1:-1]
        
        # Get top words
        top_words = [feature_names[i] for i in top_word_indices]
        
        topic_words.append(top_words)
    
    logger.info(f"Extracted top words for {len(topic_words)} topics")
    return topic_words

def assign_topics_to_articles(articles, doc_topic_matrix, threshold=0.3):
    """
    Assign topics to articles based on the document-topic matrix
    
    Args:
        articles: DataFrame containing articles
        doc_topic_matrix: Document-topic matrix from LDA
        threshold: Minimum probability threshold for topic assignment
        
    Returns:
        DataFrame with topic assignments
    """
    logger.info(f"Assigning topics to articles with threshold {threshold}")
    
    # Create a copy of the DataFrame
    topic_df = articles.copy()
    
    # Initialize topic columns
    for topic_idx in range(doc_topic_matrix.shape[1]):
        topic_df[f'topic_{topic_idx}'] = 0.0
    
    # Assign topic probabilities
    valid_indices = topic_df[topic_df['title'].fillna('') != ''].index
    
    for i, idx in enumerate(valid_indices):
        if i < len(doc_topic_matrix):
            for topic_idx in range(doc_topic_matrix.shape[1]):
                topic_df.at[idx, f'topic_{topic_idx}'] = doc_topic_matrix[i, topic_idx]
    
    # Assign primary topic
    topic_df['primary_topic'] = topic_df[[f'topic_{i}' for i in range(doc_topic_matrix.shape[1])]].idxmax(axis=1)
    topic_df['primary_topic'] = topic_df['primary_topic'].apply(lambda x: int(x.split('_')[1]) if pd.notna(x) else None)
    
    # Assign topic confidence
    topic_df['topic_confidence'] = topic_df[[f'topic_{i}' for i in range(doc_topic_matrix.shape[1])]].max(axis=1)
    
    logger.info(f"Assigned topics to {len(topic_df)} articles")
    return topic_df
