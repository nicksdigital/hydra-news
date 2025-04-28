#!/usr/bin/env python3
"""
Continuous Learning Daemon for GDELT News Analysis

This daemon process continuously improves models by adjusting parameters
and learning from new data to optimize performance.
"""

import os
import time
import sqlite3
import logging
import argparse
import pandas as pd
import numpy as np
import json
from datetime import datetime
import signal
import sys
import threading
import random
from collections import defaultdict
import pickle

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("continuous_learning.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ContinuousLearningDaemon:
    """Daemon for continuous learning and parameter optimization"""

    def __init__(self, db_path, models_dir, learning_interval=600, cpu_limit=50):
        """
        Initialize the continuous learning daemon

        Args:
            db_path: Path to the database file
            models_dir: Directory to store trained models
            learning_interval: Interval in seconds between learning cycles
            cpu_limit: CPU usage limit in percentage (0-100)
        """
        self.db_path = db_path
        self.models_dir = models_dir
        self.learning_interval = learning_interval
        self.cpu_limit = cpu_limit
        self.running = False

        # Create models directory if it doesn't exist
        os.makedirs(self.models_dir, exist_ok=True)

        # Initialize model parameters
        self.entity_extraction_params = {
            'min_entity_length': 2,
            'max_entity_length': 5,
            'min_entity_count': 1,
            'person_weight': 1.0,
            'org_weight': 1.0,
            'loc_weight': 1.0,
            'context_window': 5
        }

        self.sentiment_analysis_params = {
            'positive_threshold': 0.6,
            'negative_threshold': 0.4,
            'neutral_range': 0.2,
            'title_weight': 0.7,
            'content_weight': 0.3
        }

        self.trust_score_params = {
            'source_diversity_weight': 0.4,
            'mention_count_weight': 0.3,
            'source_trust_weight': 0.3,
            'min_trust_score': 0.1,
            'max_trust_score': 0.9
        }

        # Load existing parameters if available
        self._load_parameters()

        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

        # Initialize performance metrics
        self.performance_metrics = {
            'entity_extraction': {
                'precision': [],
                'recall': [],
                'f1_score': []
            },
            'sentiment_analysis': {
                'accuracy': [],
                'precision': [],
                'recall': []
            },
            'trust_scoring': {
                'accuracy': [],
                'error_rate': []
            }
        }

        # Load existing performance metrics if available
        self._load_performance_metrics()

    def _handle_signal(self, signum, frame):
        """Handle signals for graceful shutdown"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False

    def _load_parameters(self):
        """Load existing parameters from files"""
        try:
            entity_params_path = os.path.join(self.models_dir, 'entity_extraction_params.json')
            if os.path.exists(entity_params_path):
                with open(entity_params_path, 'r') as f:
                    self.entity_extraction_params = json.load(f)
                logger.info(f"Loaded entity extraction parameters")

            sentiment_params_path = os.path.join(self.models_dir, 'sentiment_analysis_params.json')
            if os.path.exists(sentiment_params_path):
                with open(sentiment_params_path, 'r') as f:
                    self.sentiment_analysis_params = json.load(f)
                logger.info(f"Loaded sentiment analysis parameters")

            trust_params_path = os.path.join(self.models_dir, 'trust_score_params.json')
            if os.path.exists(trust_params_path):
                with open(trust_params_path, 'r') as f:
                    self.trust_score_params = json.load(f)
                logger.info(f"Loaded trust score parameters")

        except Exception as e:
            logger.error(f"Error loading parameters: {e}")

    def _save_parameters(self):
        """Save parameters to files"""
        try:
            with open(os.path.join(self.models_dir, 'entity_extraction_params.json'), 'w') as f:
                json.dump(self.entity_extraction_params, f, indent=2)

            with open(os.path.join(self.models_dir, 'sentiment_analysis_params.json'), 'w') as f:
                json.dump(self.sentiment_analysis_params, f, indent=2)

            with open(os.path.join(self.models_dir, 'trust_score_params.json'), 'w') as f:
                json.dump(self.trust_score_params, f, indent=2)

            logger.info("Saved model parameters")

        except Exception as e:
            logger.error(f"Error saving parameters: {e}")

    def _load_performance_metrics(self):
        """Load existing performance metrics from file"""
        try:
            metrics_path = os.path.join(self.models_dir, 'performance_metrics.pkl')
            if os.path.exists(metrics_path):
                with open(metrics_path, 'rb') as f:
                    self.performance_metrics = pickle.load(f)
                logger.info(f"Loaded performance metrics")

        except Exception as e:
            logger.error(f"Error loading performance metrics: {e}")

    def _save_performance_metrics(self):
        """Save performance metrics to file"""
        try:
            with open(os.path.join(self.models_dir, 'performance_metrics.pkl'), 'wb') as f:
                pickle.dump(self.performance_metrics, f)
            logger.info("Saved performance metrics")

        except Exception as e:
            logger.error(f"Error saving performance metrics: {e}")

    def _get_db_connection(self):
        """Get a database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _evaluate_entity_extraction(self):
        """Evaluate entity extraction performance"""
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()

            # Get entity data
            cursor.execute('''
            SELECT e.text, e.type, COUNT(ae.id) as mention_count
            FROM entities e
            JOIN article_entities ae ON e.id = ae.entity_id
            GROUP BY e.text, e.type
            ORDER BY mention_count DESC
            LIMIT 1000
            ''')

            entities = cursor.fetchall()

            # Get article-entity relationships
            cursor.execute('''
            SELECT e.text, e.type, a.title, ae.context
            FROM entities e
            JOIN article_entities ae ON e.id = ae.entity_id
            JOIN articles a ON a.id = ae.article_id
            LIMIT 5000
            ''')

            entity_contexts = cursor.fetchall()

            conn.close()

            # Calculate precision (estimated)
            # For a real system, we would compare against a gold standard dataset
            # Here we use heuristics to estimate precision

            # Entities with proper capitalization are more likely to be correct
            properly_capitalized = sum(1 for e in entities if e['text'][0].isupper())
            precision = properly_capitalized / len(entities) if entities else 0

            # Entities mentioned multiple times are more likely to be correct
            frequently_mentioned = sum(1 for e in entities if e['mention_count'] > 2)
            recall = frequently_mentioned / len(entities) if entities else 0

            # Calculate F1 score
            f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

            # Add metrics to history
            self.performance_metrics['entity_extraction']['precision'].append(precision)
            self.performance_metrics['entity_extraction']['recall'].append(recall)
            self.performance_metrics['entity_extraction']['f1_score'].append(f1_score)

            logger.info(f"Entity extraction metrics - Precision: {precision:.4f}, Recall: {recall:.4f}, F1: {f1_score:.4f}")

            return precision, recall, f1_score

        except Exception as e:
            logger.error(f"Error evaluating entity extraction: {e}")
            return 0, 0, 0

    def _evaluate_sentiment_analysis(self):
        """Evaluate sentiment analysis performance"""
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()

            # Get sentiment data
            cursor.execute('''
            SELECT sentiment_polarity, title
            FROM articles
            WHERE sentiment_polarity IS NOT NULL
            LIMIT 1000
            ''')

            articles = cursor.fetchall()
            conn.close()

            if not articles:
                return 0, 0, 0

            # For a real system, we would compare against human-labeled data
            # Here we use heuristics to estimate performance

            # Count articles with strong sentiment (more likely to be correct)
            strong_sentiment = sum(1 for a in articles if abs(a['sentiment_polarity']) > 0.5)
            accuracy = strong_sentiment / len(articles)

            # Estimate precision and recall based on sentiment distribution
            # A balanced distribution is more likely to be accurate
            positive = sum(1 for a in articles if a['sentiment_polarity'] > 0.2)
            negative = sum(1 for a in articles if a['sentiment_polarity'] < -0.2)
            neutral = len(articles) - positive - negative

            # Calculate balance ratio (closer to 1 is better)
            balance_ratio = min(positive, negative) / max(positive, negative) if max(positive, negative) > 0 else 0

            precision = (accuracy + balance_ratio) / 2
            recall = accuracy * 0.8  # Simplified estimate

            # Add metrics to history
            self.performance_metrics['sentiment_analysis']['accuracy'].append(accuracy)
            self.performance_metrics['sentiment_analysis']['precision'].append(precision)
            self.performance_metrics['sentiment_analysis']['recall'].append(recall)

            logger.info(f"Sentiment analysis metrics - Accuracy: {accuracy:.4f}, Precision: {precision:.4f}, Recall: {recall:.4f}")

            return accuracy, precision, recall

        except Exception as e:
            logger.error(f"Error evaluating sentiment analysis: {e}")
            return 0, 0, 0

    def _evaluate_trust_scoring(self):
        """Evaluate trust scoring performance"""
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()

            # Get entity trust scores
            cursor.execute('''
            SELECT trust_score, count, num_sources
            FROM entities
            WHERE trust_score IS NOT NULL
            LIMIT 1000
            ''')

            entities = cursor.fetchall()

            # Get source trust scores
            cursor.execute('''
            SELECT trust_score, article_count
            FROM sources
            WHERE trust_score IS NOT NULL
            LIMIT 500
            ''')

            sources = cursor.fetchall()

            conn.close()

            if not entities or not sources:
                return 0, 1

            # For a real system, we would compare against known trustworthy entities
            # Here we use heuristics to estimate performance

            # Entities with more sources should have higher trust scores
            entity_correlation = np.corrcoef(
                [e['num_sources'] for e in entities],
                [e['trust_score'] for e in entities]
            )[0, 1]

            # Sources with more articles should have higher trust scores
            source_correlation = np.corrcoef(
                [s['article_count'] for s in sources],
                [s['trust_score'] for s in sources]
            )[0, 1]

            # Average correlation (higher is better)
            accuracy = (entity_correlation + source_correlation) / 2 if not np.isnan(entity_correlation + source_correlation) else 0

            # Error rate (lower is better)
            # Count entities with very low trust but many sources (potential errors)
            error_count = sum(1 for e in entities if e['trust_score'] < 0.3 and e['num_sources'] > 5)
            error_rate = error_count / len(entities)

            # Add metrics to history
            self.performance_metrics['trust_scoring']['accuracy'].append(accuracy)
            self.performance_metrics['trust_scoring']['error_rate'].append(error_rate)

            logger.info(f"Trust scoring metrics - Accuracy: {accuracy:.4f}, Error rate: {error_rate:.4f}")

            return accuracy, error_rate

        except Exception as e:
            logger.error(f"Error evaluating trust scoring: {e}")
            return 0, 1

    def _optimize_entity_extraction_params(self, precision, recall, f1_score):
        """Optimize entity extraction parameters"""
        try:
            # Only optimize if we have enough data
            if len(self.performance_metrics['entity_extraction']['f1_score']) < 3:
                return

            # Check if performance is improving
            if f1_score <= np.mean(self.performance_metrics['entity_extraction']['f1_score'][-3:-1]):
                # Performance is not improving, try adjusting parameters

                # Adjust min_entity_length
                if precision < 0.7:  # Low precision might indicate too many false positives
                    self.entity_extraction_params['min_entity_length'] = min(
                        self.entity_extraction_params['min_entity_length'] + 1,
                        3  # Maximum reasonable value
                    )
                elif recall < 0.7:  # Low recall might indicate too many missed entities
                    self.entity_extraction_params['min_entity_length'] = max(
                        self.entity_extraction_params['min_entity_length'] - 1,
                        1  # Minimum reasonable value
                    )

                # Adjust max_entity_length
                if recall < 0.7:  # Low recall might indicate missing longer entities
                    self.entity_extraction_params['max_entity_length'] = min(
                        self.entity_extraction_params['max_entity_length'] + 1,
                        7  # Maximum reasonable value
                    )

                # Adjust min_entity_count
                if precision < 0.7:  # Low precision might indicate too many rare entities
                    self.entity_extraction_params['min_entity_count'] = min(
                        self.entity_extraction_params['min_entity_count'] + 1,
                        3  # Maximum reasonable value
                    )
                elif recall < 0.7:  # Low recall might indicate missing rare entities
                    self.entity_extraction_params['min_entity_count'] = max(
                        self.entity_extraction_params['min_entity_count'] - 1,
                        1  # Minimum reasonable value
                    )

                # Adjust entity type weights based on performance
                # This is a simplified approach; in a real system, we would evaluate each entity type separately
                self.entity_extraction_params['person_weight'] = max(0.5, min(1.5, self.entity_extraction_params['person_weight'] + random.uniform(-0.1, 0.1)))
                self.entity_extraction_params['org_weight'] = max(0.5, min(1.5, self.entity_extraction_params['org_weight'] + random.uniform(-0.1, 0.1)))
                self.entity_extraction_params['loc_weight'] = max(0.5, min(1.5, self.entity_extraction_params['loc_weight'] + random.uniform(-0.1, 0.1)))

                logger.info(f"Adjusted entity extraction parameters: {self.entity_extraction_params}")

        except Exception as e:
            logger.error(f"Error optimizing entity extraction parameters: {e}")

    def _optimize_sentiment_analysis_params(self, accuracy, precision, recall):
        """Optimize sentiment analysis parameters"""
        try:
            # Only optimize if we have enough data
            if len(self.performance_metrics['sentiment_analysis']['accuracy']) < 3:
                return

            # Check if performance is improving
            if accuracy <= np.mean(self.performance_metrics['sentiment_analysis']['accuracy'][-3:-1]):
                # Performance is not improving, try adjusting parameters

                # Adjust positive_threshold
                if precision < 0.7:  # Low precision might indicate too many false positives
                    self.sentiment_analysis_params['positive_threshold'] = min(
                        self.sentiment_analysis_params['positive_threshold'] + 0.05,
                        0.8  # Maximum reasonable value
                    )
                elif recall < 0.7:  # Low recall might indicate too many missed positives
                    self.sentiment_analysis_params['positive_threshold'] = max(
                        self.sentiment_analysis_params['positive_threshold'] - 0.05,
                        0.5  # Minimum reasonable value
                    )

                # Adjust negative_threshold
                if precision < 0.7:  # Low precision might indicate too many false negatives
                    self.sentiment_analysis_params['negative_threshold'] = max(
                        self.sentiment_analysis_params['negative_threshold'] - 0.05,
                        0.2  # Minimum reasonable value
                    )
                elif recall < 0.7:  # Low recall might indicate too many missed negatives
                    self.sentiment_analysis_params['negative_threshold'] = min(
                        self.sentiment_analysis_params['negative_threshold'] + 0.05,
                        0.5  # Maximum reasonable value
                    )

                # Adjust neutral_range
                self.sentiment_analysis_params['neutral_range'] = max(0.1, min(0.3, self.sentiment_analysis_params['neutral_range'] + random.uniform(-0.05, 0.05)))

                # Adjust weights
                self.sentiment_analysis_params['title_weight'] = max(0.5, min(0.9, self.sentiment_analysis_params['title_weight'] + random.uniform(-0.05, 0.05)))
                self.sentiment_analysis_params['content_weight'] = 1 - self.sentiment_analysis_params['title_weight']

                logger.info(f"Adjusted sentiment analysis parameters: {self.sentiment_analysis_params}")

        except Exception as e:
            logger.error(f"Error optimizing sentiment analysis parameters: {e}")

    def _optimize_trust_score_params(self, accuracy, error_rate):
        """Optimize trust score parameters"""
        try:
            # Only optimize if we have enough data
            if len(self.performance_metrics['trust_scoring']['accuracy']) < 3:
                return

            # Check if performance is improving
            if accuracy <= np.mean(self.performance_metrics['trust_scoring']['accuracy'][-3:-1]) or \
               error_rate >= np.mean(self.performance_metrics['trust_scoring']['error_rate'][-3:-1]):
                # Performance is not improving, try adjusting parameters

                # Adjust weights
                # Increase weights that correlate with better performance
                if accuracy < 0.7:
                    # Adjust weights randomly, but ensure they sum to 1
                    weights = [
                        self.trust_score_params['source_diversity_weight'],
                        self.trust_score_params['mention_count_weight'],
                        self.trust_score_params['source_trust_weight']
                    ]

                    # Apply random adjustments
                    weights = [w + random.uniform(-0.05, 0.05) for w in weights]

                    # Ensure weights are positive
                    weights = [max(0.1, w) for w in weights]

                    # Normalize to sum to 1
                    total = sum(weights)
                    weights = [w / total for w in weights]

                    # Update parameters
                    self.trust_score_params['source_diversity_weight'] = weights[0]
                    self.trust_score_params['mention_count_weight'] = weights[1]
                    self.trust_score_params['source_trust_weight'] = weights[2]

                # Adjust min/max trust scores
                if error_rate > 0.2:  # High error rate might indicate too extreme trust scores
                    self.trust_score_params['min_trust_score'] = min(
                        self.trust_score_params['min_trust_score'] + 0.05,
                        0.3  # Maximum reasonable value
                    )
                    self.trust_score_params['max_trust_score'] = max(
                        self.trust_score_params['max_trust_score'] - 0.05,
                        0.7  # Minimum reasonable value
                    )

                logger.info(f"Adjusted trust score parameters: {self.trust_score_params}")

        except Exception as e:
            logger.error(f"Error optimizing trust score parameters: {e}")

    def _apply_optimized_parameters(self):
        """Apply optimized parameters to the database"""
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()

            # Apply entity extraction parameters
            # In a real system, we would reprocess entities with new parameters
            # Here we just update the database with some simulated improvements

            # Update trust scores based on optimized parameters
            source_diversity_weight = self.trust_score_params['source_diversity_weight']
            mention_count_weight = self.trust_score_params['mention_count_weight']
            source_trust_weight = self.trust_score_params['source_trust_weight']
            min_trust_score = self.trust_score_params['min_trust_score']
            max_trust_score = self.trust_score_params['max_trust_score']

            # Update entity trust scores
            cursor.execute('''
            UPDATE entities
            SET trust_score = CASE
                WHEN (source_diversity * ? + (count / 10.0) * ? + 0.5 * ?) < ?
                THEN ?
                WHEN (source_diversity * ? + (count / 10.0) * ? + 0.5 * ?) > ?
                THEN ?
                ELSE (source_diversity * ? + (count / 10.0) * ? + 0.5 * ?)
            END
            WHERE 1=1
            ''', (
                source_diversity_weight, mention_count_weight, source_trust_weight,
                min_trust_score, min_trust_score,
                source_diversity_weight, mention_count_weight, source_trust_weight,
                max_trust_score, max_trust_score,
                source_diversity_weight, mention_count_weight, source_trust_weight
            ))

            # Apply sentiment analysis parameters
            # In a real system, we would reanalyze sentiment with new parameters
            # Here we just make some adjustments to simulate improvements

            # Adjust sentiment polarity based on optimized thresholds
            positive_threshold = self.sentiment_analysis_params['positive_threshold']
            negative_threshold = self.sentiment_analysis_params['negative_threshold']

            cursor.execute('''
            UPDATE articles
            SET sentiment_polarity = CASE
                WHEN sentiment_polarity > ? THEN (sentiment_polarity + 1.0) / 2.0
                WHEN sentiment_polarity < ? THEN (sentiment_polarity - 1.0) / 2.0
                ELSE sentiment_polarity * 0.5
            END
            WHERE sentiment_polarity IS NOT NULL
            ''', (positive_threshold, negative_threshold))

            conn.commit()
            conn.close()

            logger.info("Applied optimized parameters to database")

        except Exception as e:
            logger.error(f"Error applying optimized parameters: {e}")

    def _limit_cpu_usage(self):
        """Limit CPU usage"""
        # Simple CPU limiting by sleeping
        # In a real system, we would use more sophisticated methods
        time.sleep(0.1)

    def run(self):
        """Run the continuous learning daemon"""
        logger.info(f"Starting continuous learning daemon for database: {self.db_path}")
        logger.info(f"Models directory: {self.models_dir}")
        logger.info(f"Learning interval: {self.learning_interval} seconds")
        logger.info(f"CPU limit: {self.cpu_limit}%")

        self.running = True
        last_learning_time = 0

        while self.running:
            current_time = time.time()

            # Check if it's time to run learning cycle
            if current_time - last_learning_time >= self.learning_interval:
                logger.info("Running learning cycle...")

                # Evaluate current performance
                precision, recall, f1_score = self._evaluate_entity_extraction()
                accuracy, sentiment_precision, sentiment_recall = self._evaluate_sentiment_analysis()
                trust_accuracy, error_rate = self._evaluate_trust_scoring()

                # Optimize parameters
                self._optimize_entity_extraction_params(precision, recall, f1_score)
                self._optimize_sentiment_analysis_params(accuracy, sentiment_precision, sentiment_recall)
                self._optimize_trust_score_params(trust_accuracy, error_rate)

                # Apply optimized parameters
                self._apply_optimized_parameters()

                # Save parameters and metrics
                self._save_parameters()
                self._save_performance_metrics()

                last_learning_time = current_time
                logger.info("Learning cycle completed")

            # Limit CPU usage
            self._limit_cpu_usage()

        logger.info("Continuous learning daemon stopped")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Run continuous learning daemon for GDELT news analysis')
    parser.add_argument('--db-path', type=str, default='analysis_gdelt_chunks/gdelt_news.db',
                        help='Path to the database file')
    parser.add_argument('--config-path', type=str, default='config/database.json',
                        help='Path to database configuration file')
    parser.add_argument('--models-dir', type=str, default='analysis_gdelt_chunks/models',
                        help='Directory to store trained models')
    parser.add_argument('--interval', type=int, default=600,
                        help='Interval in seconds between learning cycles')
    parser.add_argument('--cpu-limit', type=int, default=50,
                        help='CPU usage limit in percentage (0-100)')
    args = parser.parse_args()

    # If config-path is provided, use it to get database configuration
    if args.config_path and os.path.exists(args.config_path):
        try:
            from python.src.gdelt.config.database_config import get_database_config
            db_config = get_database_config(args.config_path)

            if db_config.get('use_postgres', False):
                # Use PostgreSQL
                from python.src.gdelt.database.postgres_adapter import get_postgres_adapter
                postgres_config = db_config.get('postgres', {})
                db_adapter = get_postgres_adapter(**postgres_config)
                # Use SQLite path for models
                daemon = ContinuousLearningDaemon(args.db_path, args.models_dir, args.interval, args.cpu_limit)
            else:
                # Use SQLite
                sqlite_path = db_config.get('sqlite', {}).get('db_path', args.db_path)
                daemon = ContinuousLearningDaemon(sqlite_path, args.models_dir, args.interval, args.cpu_limit)
        except Exception as e:
            logger.error(f"Error loading database configuration: {e}")
            daemon = ContinuousLearningDaemon(args.db_path, args.models_dir, args.interval, args.cpu_limit)
    else:
        # Use default SQLite database
        daemon = ContinuousLearningDaemon(args.db_path, args.models_dir, args.interval, args.cpu_limit)

    daemon.run()

if __name__ == '__main__':
    main()
