#!/usr/bin/env python3
"""
Run Enhanced GDELT Analysis

This script runs the enhanced GDELT data fetcher and analysis pipeline.
"""

import os
import sys
import argparse
import logging
import subprocess
import time
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Run Enhanced GDELT Analysis')
    
    # Data fetching options
    parser.add_argument('--fetch-data', action='store_true',
                        help='Fetch new data from GDELT')
    parser.add_argument('--output-dir', type=str, default='dataset_gdelt_enhanced',
                        help='Directory to save the dataset')
    parser.add_argument('--max-articles', type=int, default=4000,
                        help='Maximum number of articles to fetch')
    parser.add_argument('--timespan', type=str, default='1m',
                        help='Timespan for fetching articles (e.g., "1m" for 1 month)')
    parser.add_argument('--incremental', action='store_true',
                        help='Enable incremental fetching (only fetch new articles)')
    
    # Analysis options
    parser.add_argument('--analyze-data', action='store_true',
                        help='Analyze the fetched data')
    parser.add_argument('--analysis-dir', type=str, default='analysis_gdelt_enhanced',
                        help='Directory to save the analysis results')
    parser.add_argument('--no-sentiment', action='store_true',
                        help='Disable sentiment analysis')
    parser.add_argument('--no-topics', action='store_true',
                        help='Disable topic modeling')
    parser.add_argument('--no-entities', action='store_true',
                        help='Disable entity extraction')
    parser.add_argument('--top-entities', type=int, default=50,
                        help='Number of top entities to analyze')
    parser.add_argument('--min-mentions', type=int, default=3,
                        help='Minimum number of mentions for an entity')
    
    # Prediction options
    parser.add_argument('--predict', action='store_true',
                        help='Run prediction models')
    parser.add_argument('--days-to-predict', type=int, default=14,
                        help='Number of days to predict into the future')
    parser.add_argument('--event-threshold', type=int, default=3,
                        help='Threshold for predicting an event (number of mentions)')
    parser.add_argument('--specific-entities', type=str, nargs='+',
                        help='Specific entities to predict (if not provided, use top entities)')
    
    return parser.parse_args()

def run_fetch_data(args):
    """Run the enhanced data fetcher"""
    logger.info("Running enhanced data fetcher...")
    
    # Build command
    cmd = [
        sys.executable, 
        os.path.join('python', 'src', 'gdelt', 'fetch_gdelt_enhanced.py'),
        '--output-dir', args.output_dir,
        '--max-articles', str(args.max_articles),
        '--timespan', args.timespan
    ]
    
    if args.incremental:
        cmd.append('--incremental')
    
    # Run command
    logger.info(f"Running command: {' '.join(cmd)}")
    
    try:
        subprocess.run(cmd, check=True)
        logger.info("Data fetching completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running data fetcher: {e}")
        return False

def run_analyze_data(args):
    """Run the GDELT analyzer"""
    logger.info("Running GDELT analyzer...")
    
    # Build command
    cmd = [
        sys.executable, 
        os.path.join('python', 'src', 'gdelt', 'analyze_gdelt_all_entities.py'),
        '--dataset-dir', args.output_dir,
        '--output-dir', args.analysis_dir,
        '--top-entities', str(args.top_entities),
        '--min-mentions', str(args.min_mentions)
    ]
    
    if args.no_sentiment:
        cmd.append('--no-sentiment')
    
    if args.no_topics:
        cmd.append('--no-topics')
    
    if args.no_entities:
        cmd.append('--no-entities')
    
    # Run command
    logger.info(f"Running command: {' '.join(cmd)}")
    
    try:
        subprocess.run(cmd, check=True)
        logger.info("Data analysis completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running data analyzer: {e}")
        return False

def run_prediction(args):
    """Run prediction models"""
    logger.info("Running prediction models...")
    
    # Import prediction modules
    from python.src.gdelt.analyzer.prediction import PredictiveEventDetector
    from python.src.gdelt.analyzer.database_manager import DatabaseManager
    
    # Get database path
    db_path = os.path.join(args.analysis_dir, "gdelt_news.db")
    
    if not os.path.exists(db_path):
        logger.error(f"Database file not found: {db_path}")
        return False
    
    # Initialize database manager
    db_manager = DatabaseManager(db_path)
    if not db_manager.connect():
        logger.error("Failed to connect to database")
        return False
    
    # Initialize predictor
    predictor = PredictiveEventDetector(db_manager)
    
    # Get entities to predict
    entities = args.specific_entities
    
    if not entities:
        # Get top entities from database
        logger.info("Getting top entities from database...")
        
        try:
            # Query top entities
            query = """
            SELECT e.text, COUNT(ae.article_id) as mention_count
            FROM entities e
            JOIN article_entities ae ON e.id = ae.entity_id
            GROUP BY e.text
            HAVING COUNT(ae.article_id) >= ?
            ORDER BY mention_count DESC
            LIMIT ?
            """
            
            # Execute query
            db_manager.cursor.execute(query, (args.min_mentions, args.top_entities))
            results = db_manager.cursor.fetchall()
            
            entities = [row[0] for row in results]
            logger.info(f"Found {len(entities)} entities to predict")
        except Exception as e:
            logger.error(f"Error getting top entities: {e}")
            return False
    
    # Create predictions directory
    predictions_dir = os.path.join(args.analysis_dir, "predictions")
    os.makedirs(predictions_dir, exist_ok=True)
    
    # Run predictions for each entity
    successful_predictions = 0
    
    for entity in entities:
        logger.info(f"Predicting for entity: {entity}")
        
        try:
            # Predict entity mentions
            mention_predictions = predictor.predict_entity_mentions(
                entity,
                days_to_predict=args.days_to_predict,
                output_dir=predictions_dir
            )
            
            if mention_predictions:
                # Predict entity events
                event_predictions = predictor.predict_entity_events(
                    entity,
                    days_to_predict=args.days_to_predict,
                    event_threshold=args.event_threshold,
                    output_dir=predictions_dir
                )
                
                successful_predictions += 1
        except Exception as e:
            logger.error(f"Error predicting for entity '{entity}': {e}")
    
    # Close database connection
    db_manager.close()
    
    logger.info(f"Prediction completed for {successful_predictions} out of {len(entities)} entities")
    return successful_predictions > 0

def main():
    """Main entry point"""
    args = parse_args()
    
    # Record start time
    start_time = time.time()
    
    # Create output directories
    if args.fetch_data:
        os.makedirs(args.output_dir, exist_ok=True)
    
    if args.analyze_data or args.predict:
        os.makedirs(args.analysis_dir, exist_ok=True)
    
    # Run data fetcher
    if args.fetch_data:
        if not run_fetch_data(args):
            logger.error("Data fetching failed, aborting pipeline")
            return 1
    
    # Run data analyzer
    if args.analyze_data:
        if not run_analyze_data(args):
            logger.error("Data analysis failed, aborting pipeline")
            return 1
    
    # Run prediction models
    if args.predict:
        if not run_prediction(args):
            logger.error("Prediction failed")
            return 1
    
    # Record end time
    end_time = time.time()
    elapsed_time = end_time - start_time
    
    logger.info(f"Pipeline completed successfully in {elapsed_time:.2f} seconds")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
