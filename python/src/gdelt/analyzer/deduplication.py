#!/usr/bin/env python3
"""
GDELT Advanced Deduplication

This module provides advanced deduplication functionality for GDELT news articles.
"""

import os
import numpy as np
import pandas as pd
import logging
import sqlite3
import hashlib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re
from difflib import SequenceMatcher
from sentence_transformers import SentenceTransformer
import torch
from tqdm import tqdm

# Set up logging
logger = logging.getLogger(__name__)

class AdvancedDeduplicator:
    """Class for advanced deduplication of news articles"""

    def __init__(self, db_path=None, embedding_model="all-MiniLM-L6-v2", 
                 similarity_threshold=0.85, use_gpu=torch.cuda.is_available()):
        """
        Initialize the deduplicator

        Args:
            db_path: Path to the SQLite database
            embedding_model: Name of the sentence transformer model to use
            similarity_threshold: Threshold for considering articles as duplicates
            use_gpu: Whether to use GPU for embeddings
        """
        self.db_path = db_path
        self.similarity_threshold = similarity_threshold
        self.use_gpu = use_gpu
        
        # Initialize embedding model if available
        try:
            self.embedding_model = SentenceTransformer(embedding_model)
            if self.use_gpu:
                self.embedding_model = self.embedding_model.to('cuda')
            self.has_embedding_model = True
            logger.info(f"Initialized embedding model: {embedding_model}")
        except Exception as e:
            logger.warning(f"Could not initialize embedding model: {e}")
            self.embedding_model = None
            self.has_embedding_model = False

    def connect_to_db(self):
        """Connect to the SQLite database"""
        if not self.db_path:
            logger.warning("No database path provided")
            return False
        
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            logger.info(f"Connected to database: {self.db_path}")
            return True
        except sqlite3.Error as e:
            logger.error(f"Error connecting to database: {e}")
            return False

    def close_db_connection(self):
        """Close the database connection"""
        if hasattr(self, 'conn'):
            self.conn.close()
            logger.info("Closed database connection")

    def compute_content_hash(self, article):
        """
        Compute a hash of the article content for deduplication

        Args:
            article: Article dictionary or DataFrame row

        Returns:
            Content hash
        """
        # Combine title and URL for a more robust hash
        content = f"{article.get('title', '')}{article.get('url', '')}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()

    def normalize_text(self, text):
        """
        Normalize text for comparison

        Args:
            text: Text to normalize

        Returns:
            Normalized text
        """
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove URLs
        text = re.sub(r'https?://\S+', '', text)
        
        # Remove special characters and digits
        text = re.sub(r'[^\w\s]', '', text)
        text = re.sub(r'\d+', '', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text

    def compute_text_similarity(self, text1, text2):
        """
        Compute similarity between two texts using SequenceMatcher

        Args:
            text1: First text
            text2: Second text

        Returns:
            Similarity score (0-1)
        """
        # Normalize texts
        text1 = self.normalize_text(text1)
        text2 = self.normalize_text(text2)
        
        # Return 0 if either text is empty
        if not text1 or not text2:
            return 0
        
        # Compute similarity
        return SequenceMatcher(None, text1, text2).ratio()

    def compute_embedding(self, texts):
        """
        Compute embeddings for a list of texts

        Args:
            texts: List of texts to embed

        Returns:
            Numpy array of embeddings
        """
        if not self.has_embedding_model:
            logger.warning("No embedding model available")
            return None
        
        try:
            # Filter out None or empty texts
            valid_texts = [t for t in texts if t]
            if not valid_texts:
                return None
            
            # Compute embeddings
            embeddings = self.embedding_model.encode(valid_texts, show_progress_bar=False)
            return embeddings
        except Exception as e:
            logger.error(f"Error computing embeddings: {e}")
            return None

    def compute_embedding_similarity(self, embedding1, embedding2):
        """
        Compute cosine similarity between two embeddings

        Args:
            embedding1: First embedding
            embedding2: Second embedding

        Returns:
            Similarity score (0-1)
        """
        if embedding1 is None or embedding2 is None:
            return 0
        
        # Compute cosine similarity
        similarity = cosine_similarity(
            embedding1.reshape(1, -1),
            embedding2.reshape(1, -1)
        )[0][0]
        
        return similarity

    def is_duplicate_by_url(self, article):
        """
        Check if an article is a duplicate based on URL

        Args:
            article: Article dictionary or DataFrame row

        Returns:
            True if duplicate, False otherwise
        """
        if not hasattr(self, 'conn'):
            logger.warning("No database connection")
            return False
        
        # Get URL
        url = article.get('url', '')
        if not url:
            return False
        
        # Check if URL already exists
        self.cursor.execute('SELECT id FROM articles WHERE url = ?', (url,))
        result = self.cursor.fetchone()
        
        return result is not None

    def is_duplicate_by_content_hash(self, article):
        """
        Check if an article is a duplicate based on content hash

        Args:
            article: Article dictionary or DataFrame row

        Returns:
            True if duplicate, False otherwise
        """
        if not hasattr(self, 'conn'):
            logger.warning("No database connection")
            return False
        
        # Compute content hash
        content_hash = self.compute_content_hash(article)
        
        # Check if content hash already exists
        self.cursor.execute('SELECT id FROM articles WHERE content_hash = ?', (content_hash,))
        result = self.cursor.fetchone()
        
        return result is not None

    def is_duplicate_by_title_similarity(self, article, threshold=None):
        """
        Check if an article is a duplicate based on title similarity

        Args:
            article: Article dictionary or DataFrame row
            threshold: Similarity threshold (default: self.similarity_threshold)

        Returns:
            True if duplicate, False otherwise
        """
        if not hasattr(self, 'conn'):
            logger.warning("No database connection")
            return False
        
        # Get title
        title = article.get('title', '')
        if not title:
            return False
        
        # Use default threshold if not provided
        if threshold is None:
            threshold = self.similarity_threshold
        
        # Get recent articles
        self.cursor.execute('''
        SELECT id, title FROM articles 
        ORDER BY seendate DESC 
        LIMIT 1000
        ''')
        results = self.cursor.fetchall()
        
        # Check title similarity
        for article_id, article_title in results:
            similarity = self.compute_text_similarity(title, article_title)
            if similarity >= threshold:
                return True
        
        return False

    def is_duplicate_by_embedding(self, article, threshold=None):
        """
        Check if an article is a duplicate based on embedding similarity

        Args:
            article: Article dictionary or DataFrame row
            threshold: Similarity threshold (default: self.similarity_threshold)

        Returns:
            True if duplicate, False otherwise
        """
        if not hasattr(self, 'conn') or not self.has_embedding_model:
            logger.warning("No database connection or embedding model")
            return False
        
        # Get title
        title = article.get('title', '')
        if not title:
            return False
        
        # Use default threshold if not provided
        if threshold is None:
            threshold = self.similarity_threshold
        
        # Compute embedding for the article
        article_embedding = self.compute_embedding([title])[0]
        
        # Get recent articles with embeddings
        self.cursor.execute('''
        SELECT id, title, embedding FROM articles 
        WHERE embedding IS NOT NULL
        ORDER BY seendate DESC 
        LIMIT 1000
        ''')
        results = self.cursor.fetchall()
        
        # Check embedding similarity
        for article_id, article_title, article_embedding_str in results:
            if article_embedding_str:
                try:
                    # Convert embedding string to numpy array
                    db_embedding = np.frombuffer(article_embedding_str, dtype=np.float32)
                    
                    # Compute similarity
                    similarity = self.compute_embedding_similarity(article_embedding, db_embedding)
                    
                    if similarity >= threshold:
                        return True
                except Exception as e:
                    logger.error(f"Error comparing embeddings: {e}")
        
        return False

    def is_duplicate(self, article):
        """
        Check if an article is a duplicate using multiple methods

        Args:
            article: Article dictionary or DataFrame row

        Returns:
            True if duplicate, False otherwise
        """
        # Check by URL
        if self.is_duplicate_by_url(article):
            return True
        
        # Check by content hash
        if self.is_duplicate_by_content_hash(article):
            return True
        
        # Check by title similarity
        if self.is_duplicate_by_title_similarity(article):
            return True
        
        # Check by embedding similarity if available
        if self.has_embedding_model and self.is_duplicate_by_embedding(article):
            return True
        
        return False

    def deduplicate_dataframe(self, df):
        """
        Deduplicate a DataFrame of articles

        Args:
            df: DataFrame of articles

        Returns:
            Deduplicated DataFrame
        """
        if df.empty:
            return df
        
        # Connect to database if not already connected
        if not hasattr(self, 'conn'):
            self.connect_to_db()
        
        # Create a copy of the DataFrame
        df_copy = df.copy()
        
        # Add content hash column
        df_copy['content_hash'] = df_copy.apply(self.compute_content_hash, axis=1)
        
        # First deduplicate by URL and content hash
        df_copy = df_copy.drop_duplicates(subset=['url'])
        df_copy = df_copy.drop_duplicates(subset=['content_hash'])
        
        # Then check against database
        if hasattr(self, 'conn'):
            # Filter out duplicates
            df_copy['is_duplicate'] = df_copy.apply(self.is_duplicate, axis=1)
            df_copy = df_copy[~df_copy['is_duplicate']]
            df_copy = df_copy.drop(columns=['is_duplicate'])
        
        logger.info(f"Deduplicated DataFrame from {len(df)} to {len(df_copy)} articles")
        
        return df_copy

    def add_embeddings_to_database(self, batch_size=1000):
        """
        Add embeddings to articles in the database

        Args:
            batch_size: Number of articles to process at once

        Returns:
            Number of articles processed
        """
        if not hasattr(self, 'conn') or not self.has_embedding_model:
            logger.warning("No database connection or embedding model")
            return 0
        
        # Check if embedding column exists
        self.cursor.execute("PRAGMA table_info(articles)")
        columns = [row[1] for row in self.cursor.fetchall()]
        
        if 'embedding' not in columns:
            # Add embedding column
            self.cursor.execute("ALTER TABLE articles ADD COLUMN embedding BLOB")
            self.conn.commit()
            logger.info("Added embedding column to articles table")
        
        # Get articles without embeddings
        self.cursor.execute('''
        SELECT id, title FROM articles 
        WHERE embedding IS NULL AND title IS NOT NULL
        ''')
        articles = self.cursor.fetchall()
        
        if not articles:
            logger.info("No articles without embeddings")
            return 0
        
        logger.info(f"Adding embeddings to {len(articles)} articles")
        
        # Process articles in batches
        processed_count = 0
        
        for i in range(0, len(articles), batch_size):
            batch = articles[i:i+batch_size]
            
            # Get article IDs and titles
            article_ids = [article[0] for article in batch]
            article_titles = [article[1] for article in batch]
            
            # Compute embeddings
            embeddings = self.compute_embedding(article_titles)
            
            if embeddings is not None:
                # Update database
                for j, article_id in enumerate(article_ids):
                    # Convert embedding to bytes
                    embedding_bytes = embeddings[j].astype(np.float32).tobytes()
                    
                    # Update article
                    self.cursor.execute(
                        "UPDATE articles SET embedding = ? WHERE id = ?",
                        (embedding_bytes, article_id)
                    )
                
                self.conn.commit()
                processed_count += len(batch)
                
                logger.info(f"Added embeddings to {processed_count} articles")
        
        return processed_count

    def find_duplicates_in_database(self, threshold=None, batch_size=1000):
        """
        Find duplicates in the database

        Args:
            threshold: Similarity threshold (default: self.similarity_threshold)
            batch_size: Number of articles to process at once

        Returns:
            DataFrame with duplicate pairs
        """
        if not hasattr(self, 'conn'):
            logger.warning("No database connection")
            return pd.DataFrame()
        
        # Use default threshold if not provided
        if threshold is None:
            threshold = self.similarity_threshold
        
        # Get all articles
        self.cursor.execute('''
        SELECT id, url, title, content_hash FROM articles
        ''')
        articles = self.cursor.fetchall()
        
        if not articles:
            logger.info("No articles in database")
            return pd.DataFrame()
        
        logger.info(f"Finding duplicates among {len(articles)} articles")
        
        # Create DataFrame
        df = pd.DataFrame(articles, columns=['id', 'url', 'title', 'content_hash'])
        
        # Find duplicates by content hash
        content_hash_duplicates = df[df.duplicated(subset=['content_hash'], keep=False)].sort_values('content_hash')
        
        # Find duplicates by URL
        url_duplicates = df[df.duplicated(subset=['url'], keep=False)].sort_values('url')
        
        # Combine duplicates
        duplicates = pd.concat([content_hash_duplicates, url_duplicates]).drop_duplicates()
        
        logger.info(f"Found {len(duplicates)} potential duplicates by hash and URL")
        
        # Find duplicates by title similarity
        title_duplicates = []
        
        # Process articles in batches
        for i in tqdm(range(0, len(df), batch_size), desc="Finding title duplicates"):
            batch = df.iloc[i:i+batch_size]
            
            for _, article1 in batch.iterrows():
                for _, article2 in df.iterrows():
                    # Skip same article
                    if article1['id'] == article2['id']:
                        continue
                    
                    # Skip if already identified as duplicates
                    if article1['content_hash'] == article2['content_hash'] or article1['url'] == article2['url']:
                        continue
                    
                    # Check title similarity
                    similarity = self.compute_text_similarity(article1['title'], article2['title'])
                    
                    if similarity >= threshold:
                        title_duplicates.append({
                            'id1': article1['id'],
                            'id2': article2['id'],
                            'title1': article1['title'],
                            'title2': article2['title'],
                            'similarity': similarity
                        })
        
        # Create DataFrame for title duplicates
        title_duplicates_df = pd.DataFrame(title_duplicates)
        
        logger.info(f"Found {len(title_duplicates_df)} potential duplicates by title similarity")
        
        return title_duplicates_df

    def merge_duplicates(self, duplicate_pairs):
        """
        Merge duplicate articles in the database

        Args:
            duplicate_pairs: DataFrame with duplicate pairs

        Returns:
            Number of merged duplicates
        """
        if not hasattr(self, 'conn'):
            logger.warning("No database connection")
            return 0
        
        if duplicate_pairs.empty:
            logger.info("No duplicates to merge")
            return 0
        
        logger.info(f"Merging {len(duplicate_pairs)} duplicate pairs")
        
        # Process each duplicate pair
        merged_count = 0
        
        for _, row in duplicate_pairs.iterrows():
            try:
                # Get article IDs
                id1 = row['id1']
                id2 = row['id2']
                
                # Determine which article to keep (keep the one with more data)
                self.cursor.execute('''
                SELECT a.id, COUNT(ae.entity_id) as entity_count
                FROM articles a
                LEFT JOIN article_entities ae ON a.id = ae.article_id
                WHERE a.id IN (?, ?)
                GROUP BY a.id
                ORDER BY entity_count DESC
                ''', (id1, id2))
                
                results = self.cursor.fetchall()
                
                if not results:
                    continue
                
                # Keep the article with more entities
                keep_id = results[0][0]
                delete_id = id2 if keep_id == id1 else id1
                
                # Update article_entities to point to the kept article
                self.cursor.execute('''
                UPDATE article_entities
                SET article_id = ?
                WHERE article_id = ?
                ''', (keep_id, delete_id))
                
                # Delete the duplicate article
                self.cursor.execute('''
                DELETE FROM articles
                WHERE id = ?
                ''', (delete_id,))
                
                self.conn.commit()
                merged_count += 1
                
                if merged_count % 100 == 0:
                    logger.info(f"Merged {merged_count} duplicates")
            except Exception as e:
                logger.error(f"Error merging duplicates: {e}")
                self.conn.rollback()
        
        logger.info(f"Merged {merged_count} duplicates")
        
        return merged_count
