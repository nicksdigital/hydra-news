#!/usr/bin/env python3
"""
Run Advanced Event Detection

This script runs advanced event detection on GDELT news data.
"""

import os
import sys
import argparse
import logging
from datetime import datetime, timedelta

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Run Advanced Event Detection')
    
    # Database options
    parser.add_argument('--db-path', type=str, default='analysis_gdelt_enhanced/gdelt_news.db',
                        help='Path to the SQLite database')
    
    # Output options
    parser.add_argument('--output-dir', type=str, default='analysis_gdelt_enhanced/events',
                        help='Directory to save the event detection results')
    
    # Entity options
    parser.add_argument('--entities', type=str, nargs='+',
                        help='Specific entities to analyze')
    parser.add_argument('--top-entities', type=int, default=20,
                        help='Number of top entities to analyze if no specific entities provided')
    parser.add_argument('--min-mentions', type=int, default=10,
                        help='Minimum number of mentions for an entity to be included')
    
    # Date range options
    parser.add_argument('--start-date', type=str,
                        help='Start date for analysis (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str,
                        help='End date for analysis (YYYY-MM-DD)')
    parser.add_argument('--days-back', type=int, default=30,
                        help='Number of days to look back if no start date provided')
    
    # Detection options
    parser.add_argument('--detection-methods', type=str, nargs='+',
                        default=['anomaly', 'burst', 'change_point'],
                        help='Detection methods to use')
    parser.add_argument('--min-correlation', type=float, default=0.7,
                        help='Minimum correlation coefficient for multi-entity analysis')
    parser.add_argument('--max-lag', type=int, default=7,
                        help='Maximum lag for causal analysis (in days)')
    
    # Analysis types
    parser.add_argument('--entity-events', action='store_true',
                        help='Detect events for individual entities')
    parser.add_argument('--correlated-events', action='store_true',
                        help='Detect correlated events between entities')
    parser.add_argument('--co-occurring-events', action='store_true',
                        help='Detect co-occurring events between entities')
    parser.add_argument('--causal-events', action='store_true',
                        help='Detect potential causal relationships between entities')
    parser.add_argument('--all-analyses', action='store_true',
                        help='Run all types of analyses')
    
    return parser.parse_args()

def get_top_entities(db_manager, top_n=20, min_mentions=10):
    """
    Get top entities from the database
    
    Args:
        db_manager: Database manager
        top_n: Number of top entities to get
        min_mentions: Minimum number of mentions
        
    Returns:
        List of entity texts
    """
    logger.info(f"Getting top {top_n} entities with at least {min_mentions} mentions")
    
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
    db_manager.cursor.execute(query, (min_mentions, top_n))
    results = db_manager.cursor.fetchall()
    
    # Extract entity texts
    entities = [row[0] for row in results]
    
    logger.info(f"Found {len(entities)} entities")
    
    return entities

def main():
    """Main entry point"""
    args = parse_args()
    
    # Import modules
    from python.src.gdelt.analyzer.database_manager import DatabaseManager
    from python.src.gdelt.analyzer.event_detection import EntityEventDetector, MultiEntityEventDetector
    
    # Connect to database
    db_manager = DatabaseManager(args.db_path)
    if not db_manager.connect():
        logger.error(f"Failed to connect to database: {args.db_path}")
        return 1
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Get entities to analyze
    entities = args.entities
    
    if not entities:
        # Get top entities from database
        entities = get_top_entities(
            db_manager,
            top_n=args.top_entities,
            min_mentions=args.min_mentions
        )
        
    if not entities:
        logger.error("No entities to analyze")
        return 1
    
    # Parse date range
    start_date = args.start_date
    end_date = args.end_date
    
    if not start_date:
        # Calculate start date based on days back
        start_date = (datetime.now() - timedelta(days=args.days_back)).strftime('%Y-%m-%d')
        
    if not end_date:
        # Use current date as end date
        end_date = datetime.now().strftime('%Y-%m-%d')
        
    logger.info(f"Analyzing data from {start_date} to {end_date}")
    
    # Initialize detectors
    entity_detector = EntityEventDetector(db_manager)
    multi_entity_detector = MultiEntityEventDetector(db_manager)
    
    # Run entity event detection
    if args.entity_events or args.all_analyses:
        logger.info("Running entity event detection")
        
        entity_results = entity_detector.detect_events_for_multiple_entities(
            entities,
            start_date=start_date,
            end_date=end_date,
            detection_methods=args.detection_methods,
            output_dir=os.path.join(args.output_dir, 'entity_events')
        )
        
        logger.info(f"Detected events for {len(entity_results)} entities")
    
    # Run correlated events detection
    if args.correlated_events or args.all_analyses:
        logger.info("Running correlated events detection")
        
        correlated_results = multi_entity_detector.detect_correlated_events(
            entities,
            start_date=start_date,
            end_date=end_date,
            min_correlation=args.min_correlation,
            output_dir=os.path.join(args.output_dir, 'correlated_events')
        )
        
        if correlated_results:
            logger.info(f"Detected {len(correlated_results.get('correlated_pairs', []))} correlated entity pairs")
    
    # Run co-occurring events detection
    if args.co_occurring_events or args.all_analyses:
        logger.info("Running co-occurring events detection")
        
        co_occurring_results = multi_entity_detector.detect_co_occurring_events(
            entities,
            start_date=start_date,
            end_date=end_date,
            output_dir=os.path.join(args.output_dir, 'co_occurring_events')
        )
        
        if co_occurring_results:
            logger.info(f"Detected {len(co_occurring_results.get('co_occurring_events', []))} co-occurring events")
    
    # Run causal events detection
    if args.causal_events or args.all_analyses:
        logger.info("Running causal events detection")
        
        causal_results = multi_entity_detector.detect_causal_events(
            entities,
            start_date=start_date,
            end_date=end_date,
            max_lag=args.max_lag,
            min_correlation=args.min_correlation,
            output_dir=os.path.join(args.output_dir, 'causal_events')
        )
        
        if causal_results:
            logger.info(f"Detected {len(causal_results.get('causal_relationships', []))} potential causal relationships")
    
    # Close database connection
    db_manager.close()
    
    logger.info("Event detection completed successfully")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
