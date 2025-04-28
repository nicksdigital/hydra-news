#!/usr/bin/env python3
"""
Optimization Daemon for GDELT News Analysis

This daemon process continuously optimizes entity extraction and sentiment analysis
by monitoring the database and improving entity recognition over time.
"""

import os
import time
import sqlite3
import logging
import argparse
import pandas as pd
import json
from collections import Counter, defaultdict
from datetime import datetime
import signal
import sys

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("optimization_daemon.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class OptimizationDaemon:
    """Daemon for optimizing entity extraction and sentiment analysis"""

    def __init__(self, db_path, optimization_interval=300, entity_lists_path='entity_lists'):
        """
        Initialize the optimization daemon

        Args:
            db_path: Path to the database file
            optimization_interval: Interval in seconds between optimization runs
            entity_lists_path: Path to store optimized entity lists
        """
        self.db_path = db_path
        self.optimization_interval = optimization_interval
        self.entity_lists_path = entity_lists_path
        self.running = False

        # Create entity lists directory if it doesn't exist
        os.makedirs(self.entity_lists_path, exist_ok=True)

        # Initialize entity lists
        self.person_entities = set()
        self.organization_entities = set()
        self.location_entities = set()
        self.ambiguous_entities = set()

        # Load existing entity lists if available
        self._load_entity_lists()

        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

    def _handle_signal(self, signum, frame):
        """Handle signals for graceful shutdown"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False

    def _load_entity_lists(self):
        """Load existing entity lists from files"""
        try:
            person_path = os.path.join(self.entity_lists_path, 'person_entities.json')
            if os.path.exists(person_path):
                with open(person_path, 'r') as f:
                    self.person_entities = set(json.load(f))
                logger.info(f"Loaded {len(self.person_entities)} person entities")

            org_path = os.path.join(self.entity_lists_path, 'organization_entities.json')
            if os.path.exists(org_path):
                with open(org_path, 'r') as f:
                    self.organization_entities = set(json.load(f))
                logger.info(f"Loaded {len(self.organization_entities)} organization entities")

            loc_path = os.path.join(self.entity_lists_path, 'location_entities.json')
            if os.path.exists(loc_path):
                with open(loc_path, 'r') as f:
                    self.location_entities = set(json.load(f))
                logger.info(f"Loaded {len(self.location_entities)} location entities")

            ambig_path = os.path.join(self.entity_lists_path, 'ambiguous_entities.json')
            if os.path.exists(ambig_path):
                with open(ambig_path, 'r') as f:
                    self.ambiguous_entities = set(json.load(f))
                logger.info(f"Loaded {len(self.ambiguous_entities)} ambiguous entities")

        except Exception as e:
            logger.error(f"Error loading entity lists: {e}")

    def _save_entity_lists(self):
        """Save entity lists to files"""
        try:
            with open(os.path.join(self.entity_lists_path, 'person_entities.json'), 'w') as f:
                json.dump(list(self.person_entities), f)

            with open(os.path.join(self.entity_lists_path, 'organization_entities.json'), 'w') as f:
                json.dump(list(self.organization_entities), f)

            with open(os.path.join(self.entity_lists_path, 'location_entities.json'), 'w') as f:
                json.dump(list(self.location_entities), f)

            with open(os.path.join(self.entity_lists_path, 'ambiguous_entities.json'), 'w') as f:
                json.dump(list(self.ambiguous_entities), f)

            logger.info("Saved entity lists")

        except Exception as e:
            logger.error(f"Error saving entity lists: {e}")

    def _get_db_connection(self, timeout=30, retries=3):
        """
        Get a database connection with retry logic

        Args:
            timeout: Connection timeout in seconds
            retries: Number of retries if connection fails

        Returns:
            SQLite connection object
        """
        for attempt in range(retries):
            try:
                conn = sqlite3.connect(self.db_path, timeout=timeout)
                conn.row_factory = sqlite3.Row
                # Enable foreign keys
                conn.execute("PRAGMA foreign_keys = ON")
                # Set journal mode to WAL for better concurrency
                conn.execute("PRAGMA journal_mode = WAL")
                # Set busy timeout
                conn.execute(f"PRAGMA busy_timeout = {timeout * 1000}")
                return conn
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e) and attempt < retries - 1:
                    logger.warning(f"Database is locked, retrying in 2 seconds (attempt {attempt + 1}/{retries})")
                    time.sleep(2)
                else:
                    raise

    def _analyze_entity_types(self):
        """Analyze entity types in the database"""
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()

            # Get all entities
            cursor.execute('''
            SELECT text, type, count, trust_score
            FROM entities
            ORDER BY count DESC
            ''')

            entities = cursor.fetchall()

            # Count entity types
            entity_types = Counter()
            for entity in entities:
                entity_types[entity['type']] += 1

            logger.info(f"Entity type distribution: {dict(entity_types)}")

            # Get entity-article relationships
            cursor.execute('''
            SELECT e.text, e.type, a.title, a.domain
            FROM entities e
            JOIN article_entities ae ON e.id = ae.entity_id
            JOIN articles a ON a.id = ae.article_id
            ''')

            entity_contexts = cursor.fetchall()

            # Analyze entity contexts
            entity_type_contexts = defaultdict(list)
            for context in entity_contexts:
                entity_type_contexts[(context['text'], context['type'])].append(context['title'])

            conn.close()

            return entities, entity_type_contexts

        except Exception as e:
            logger.error(f"Error analyzing entity types: {e}")
            return [], {}

    def _optimize_entity_types(self, entities, entity_contexts):
        """
        Optimize entity types based on context analysis

        Args:
            entities: List of entities from the database
            entity_contexts: Dictionary mapping (entity_text, entity_type) to list of contexts
        """
        try:
            # Identify potential misclassifications
            reclassifications = []

            for entity in entities:
                entity_text = entity['text']
                entity_type = entity['type']

                # Skip entities with high trust score
                if entity['trust_score'] > 0.8:
                    continue

                # Check if entity is in our curated lists
                if entity_text in self.person_entities and entity_type != 'PERSON':
                    reclassifications.append((entity_text, entity_type, 'PERSON'))
                elif entity_text in self.organization_entities and entity_type != 'ORGANIZATION':
                    reclassifications.append((entity_text, entity_type, 'ORGANIZATION'))
                elif entity_text in self.location_entities and entity_type != 'LOCATION':
                    reclassifications.append((entity_text, entity_type, 'LOCATION'))
                elif entity_text in self.ambiguous_entities:
                    continue
                else:
                    # Analyze contexts for this entity
                    contexts = entity_contexts.get((entity_text, entity_type), [])

                    # Skip entities with few contexts
                    if len(contexts) < 3:
                        continue

                    # Apply heuristics to determine correct type
                    person_indicators = ['said', 'says', 'told', 'announced', 'stated', 'claimed', 'according to']
                    org_indicators = ['announced', 'reported', 'released', 'launched', 'published', 'issued']
                    loc_indicators = ['in', 'at', 'from', 'to', 'near', 'located']

                    person_score = 0
                    org_score = 0
                    loc_score = 0

                    for context in contexts:
                        context_lower = context.lower()

                        # Check for person indicators
                        for indicator in person_indicators:
                            if f"{entity_text.lower()} {indicator}" in context_lower:
                                person_score += 1

                        # Check for organization indicators
                        for indicator in org_indicators:
                            if f"{entity_text.lower()} {indicator}" in context_lower:
                                org_score += 1

                        # Check for location indicators
                        for indicator in loc_indicators:
                            if f"{indicator} {entity_text.lower()}" in context_lower:
                                loc_score += 1

                    # Determine most likely type
                    max_score = max(person_score, org_score, loc_score)
                    if max_score > 0:
                        if person_score == max_score and entity_type != 'PERSON':
                            reclassifications.append((entity_text, entity_type, 'PERSON'))
                            self.person_entities.add(entity_text)
                        elif org_score == max_score and entity_type != 'ORGANIZATION':
                            reclassifications.append((entity_text, entity_type, 'ORGANIZATION'))
                            self.organization_entities.add(entity_text)
                        elif loc_score == max_score and entity_type != 'LOCATION':
                            reclassifications.append((entity_text, entity_type, 'LOCATION'))
                            self.location_entities.add(entity_text)

            logger.info(f"Found {len(reclassifications)} entities to reclassify")

            # Apply reclassifications to the database
            if reclassifications:
                conn = self._get_db_connection()
                cursor = conn.cursor()

                for entity_text, old_type, new_type in reclassifications:
                    logger.info(f"Reclassifying '{entity_text}' from {old_type} to {new_type}")

                    # Update entity type
                    cursor.execute('''
                    UPDATE entities
                    SET type = ?
                    WHERE text = ? AND type = ?
                    ''', (new_type, entity_text, old_type))

                conn.commit()
                conn.close()

                # Save updated entity lists
                self._save_entity_lists()

        except Exception as e:
            logger.error(f"Error optimizing entity types: {e}")

    def _optimize_entity_merging(self):
        """Optimize entity extraction by merging similar entities"""
        conn = None
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()

            # Begin transaction
            conn.execute("BEGIN TRANSACTION")

            # Find potential duplicate entities (same type, similar text)
            cursor.execute('''
            SELECT e1.id as id1, e1.text as text1, e2.id as id2, e2.text as text2, e1.type
            FROM entities e1
            JOIN entities e2 ON e1.type = e2.type AND e1.id < e2.id
            WHERE (
                e1.text LIKE e2.text || '%' OR
                e2.text LIKE e1.text || '%' OR
                e1.text LIKE '% ' || e2.text OR
                e2.text LIKE '% ' || e1.text
            )
            AND length(e1.text) > 3 AND length(e2.text) > 3
            LIMIT 100  -- Process in smaller batches to avoid long transactions
            ''')

            potential_merges = cursor.fetchall()
            logger.info(f"Found {len(potential_merges)} potential entity merges")

            # Apply merges
            merges_applied = 0
            for merge in potential_merges:
                # Determine which entity to keep (usually the longer one)
                if len(merge['text1']) >= len(merge['text2']):
                    keep_id, keep_text = merge['id1'], merge['text1']
                    merge_id, merge_text = merge['id2'], merge['text2']
                else:
                    keep_id, keep_text = merge['id2'], merge['text2']
                    merge_id, merge_text = merge['id1'], merge['text1']

                # Skip if texts are too different
                if len(keep_text) > 2 * len(merge_text) or len(merge_text) > 2 * len(keep_text):
                    continue

                logger.info(f"Merging entity '{merge_text}' into '{keep_text}'")

                try:
                    # First, find any duplicate article-entity relationships that would be created
                    cursor.execute('''
                    SELECT ae.article_id
                    FROM article_entities ae
                    WHERE ae.entity_id = ?
                    AND ae.article_id IN (
                        SELECT article_id
                        FROM article_entities
                        WHERE entity_id = ?
                    )
                    ''', (merge_id, keep_id))

                    # Get articles that have both entities (would cause constraint violation)
                    duplicate_articles = [row[0] for row in cursor.fetchall()]

                    # Delete the duplicate relationships to avoid constraint violations
                    if duplicate_articles:
                        placeholders = ','.join(['?'] * len(duplicate_articles))
                        cursor.execute(f'''
                        DELETE FROM article_entities
                        WHERE entity_id = ?
                        AND article_id IN ({placeholders})
                        ''', [merge_id] + duplicate_articles)

                    # Update remaining article_entities to point to the kept entity
                    cursor.execute('''
                    UPDATE article_entities
                    SET entity_id = ?
                    WHERE entity_id = ?
                    ''', (keep_id, merge_id))

                    # Delete the merged entity
                    cursor.execute('''
                    DELETE FROM entities
                    WHERE id = ?
                    ''', (merge_id,))

                    merges_applied += 1

                except sqlite3.IntegrityError as e:
                    logger.warning(f"Integrity error while merging '{merge_text}' into '{keep_text}': {e}")
                    # Skip this merge but continue with others
                    continue
                except sqlite3.OperationalError as e:
                    if "database is locked" in str(e):
                        logger.warning(f"Database is locked during merge, will retry in next cycle")
                        # Rollback and exit
                        if conn:
                            conn.rollback()
                        return
                    else:
                        raise

            # Commit changes
            conn.commit()
            logger.info(f"Applied {merges_applied} entity merges")

        except Exception as e:
            logger.error(f"Error optimizing entity merging: {e}")
            # Rollback on error
            if conn:
                try:
                    conn.rollback()
                except:
                    pass
        finally:
            # Close connection
            if conn:
                try:
                    conn.close()
                except:
                    pass

    def _optimize_trust_scores(self):
        """Optimize trust scores for entities and sources"""
        conn = None
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()

            # Begin transaction
            conn.execute("BEGIN TRANSACTION")

            # Update entity trust scores based on source diversity
            cursor.execute('''
            UPDATE entities
            SET trust_score = CASE
                WHEN num_sources > 10 THEN 0.9
                WHEN num_sources > 5 THEN 0.8
                WHEN num_sources > 3 THEN 0.7
                WHEN num_sources > 1 THEN 0.6
                ELSE 0.5
            END
            WHERE 1=1
            ''')

            # Update source trust scores based on article count
            cursor.execute('''
            UPDATE sources
            SET trust_score = CASE
                WHEN article_count > 50 THEN 0.9
                WHEN article_count > 20 THEN 0.8
                WHEN article_count > 10 THEN 0.7
                WHEN article_count > 5 THEN 0.6
                ELSE 0.5
            END
            WHERE 1=1
            ''')

            # Commit changes
            conn.commit()
            logger.info("Updated trust scores for entities and sources")

        except sqlite3.OperationalError as e:
            if "database is locked" in str(e):
                logger.warning("Database is locked during trust score update, will retry in next cycle")
                # Rollback and exit
                if conn:
                    try:
                        conn.rollback()
                    except:
                        pass
            else:
                logger.error(f"Error optimizing trust scores: {e}")
                # Rollback on error
                if conn:
                    try:
                        conn.rollback()
                    except:
                        pass
        except Exception as e:
            logger.error(f"Error optimizing trust scores: {e}")
            # Rollback on error
            if conn:
                try:
                    conn.rollback()
                except:
                    pass
        finally:
            # Close connection
            if conn:
                try:
                    conn.close()
                except:
                    pass

    def _update_entity_lists(self):
        """Update entity lists based on database content"""
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()

            # Get high-confidence entities
            cursor.execute('''
            SELECT text, type, trust_score
            FROM entities
            WHERE trust_score > 0.7
            ''')

            high_confidence_entities = cursor.fetchall()

            # Update entity lists
            for entity in high_confidence_entities:
                if entity['type'] == 'PERSON':
                    self.person_entities.add(entity['text'])
                elif entity['type'] == 'ORGANIZATION':
                    self.organization_entities.add(entity['text'])
                elif entity['type'] == 'LOCATION':
                    self.location_entities.add(entity['text'])

            conn.close()

            # Save updated entity lists
            self._save_entity_lists()

            logger.info(f"Updated entity lists: {len(self.person_entities)} persons, "
                       f"{len(self.organization_entities)} organizations, "
                       f"{len(self.location_entities)} locations")

        except Exception as e:
            logger.error(f"Error updating entity lists: {e}")

    def run(self):
        """Run the optimization daemon"""
        logger.info(f"Starting optimization daemon for database: {self.db_path}")
        logger.info(f"Optimization interval: {self.optimization_interval} seconds")

        self.running = True
        last_run_time = 0

        while self.running:
            current_time = time.time()

            # Check if it's time to run optimization
            if current_time - last_run_time >= self.optimization_interval:
                logger.info("Running optimization...")

                # Analyze entity types
                entities, entity_contexts = self._analyze_entity_types()

                # Optimize entity types
                self._optimize_entity_types(entities, entity_contexts)
                # Add a small delay to avoid database contention
                time.sleep(2)

                # Optimize entity merging
                self._optimize_entity_merging()
                # Add a small delay to avoid database contention
                time.sleep(2)

                # Optimize trust scores
                self._optimize_trust_scores()
                # Add a small delay to avoid database contention
                time.sleep(2)

                # Update entity lists
                self._update_entity_lists()

                last_run_time = current_time
                logger.info("Optimization completed")

            # Sleep for a short time
            time.sleep(10)

        logger.info("Optimization daemon stopped")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Run optimization daemon for GDELT news analysis')
    parser.add_argument('--db-path', type=str, default='analysis_gdelt_chunks/gdelt_news.db',
                        help='Path to the database file')
    parser.add_argument('--config-path', type=str, default='config/database.json',
                        help='Path to database configuration file')
    parser.add_argument('--interval', type=int, default=300,
                        help='Interval in seconds between optimization runs')
    parser.add_argument('--entity-lists-path', type=str, default='analysis_gdelt_chunks/entity_lists',
                        help='Path to store optimized entity lists')
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
                # Use SQLite path for entity lists
                daemon = OptimizationDaemon(args.db_path, args.interval, args.entity_lists_path)
            else:
                # Use SQLite
                sqlite_path = db_config.get('sqlite', {}).get('db_path', args.db_path)
                daemon = OptimizationDaemon(sqlite_path, args.interval, args.entity_lists_path)
        except Exception as e:
            logger.error(f"Error loading database configuration: {e}")
            daemon = OptimizationDaemon(args.db_path, args.interval, args.entity_lists_path)
    else:
        # Use default SQLite database
        daemon = OptimizationDaemon(args.db_path, args.interval, args.entity_lists_path)

    daemon.run()

if __name__ == '__main__':
    main()
