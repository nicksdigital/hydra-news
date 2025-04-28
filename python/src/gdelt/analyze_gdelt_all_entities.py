#!/usr/bin/env python3
"""
GDELT Analyzer for All Entities

This script analyzes a GDELT dataset and generates timelines for all top entities.
"""

import os
import sys
import argparse
import sqlite3
import pandas as pd
import logging
from python.src.gdelt.analyzer.core import analyze_gdelt_dataset, setup_logging

def get_top_entities(db_path, limit=50, min_mentions=3):
    """
    Get top entities from the database
    
    Args:
        db_path: Path to the SQLite database
        limit: Maximum number of entities to return
        min_mentions: Minimum number of mentions for an entity
        
    Returns:
        List of entity names
    """
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        
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
        df = pd.read_sql_query(query, conn, params=(min_mentions, limit))
        
        # Close connection
        conn.close()
        
        # Return entity names
        return df['text'].tolist()
    except Exception as e:
        logging.error(f"Error getting top entities: {e}")
        return []

def main():
    """Main entry point"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Analyze GDELT dataset with all entities")
    parser.add_argument("--dataset-dir", default="dataset_gdelt_large3", help="Directory containing the dataset")
    parser.add_argument("--output-dir", default="analysis_gdelt_all_entities", help="Directory to save the analysis results")
    parser.add_argument("--log-file", default=None, help="Path to log file")
    parser.add_argument("--no-sentiment", action="store_true", help="Disable sentiment analysis")
    parser.add_argument("--no-topics", action="store_true", help="Disable topic modeling")
    parser.add_argument("--n-topics", type=int, default=10, help="Number of topics for topic modeling")
    parser.add_argument("--no-entities", action="store_true", help="Disable entity extraction")
    parser.add_argument("--no-database", action="store_true", help="Disable database storage")
    parser.add_argument("--db-path", default=None, help="Path to the SQLite database file")
    parser.add_argument("--top-entities", type=int, default=50, help="Number of top entities to analyze")
    parser.add_argument("--min-mentions", type=int, default=3, help="Minimum number of mentions for an entity")
    parser.add_argument("--batch-size", type=int, default=10, help="Number of entities to process in each batch")
    args = parser.parse_args()
    
    # Set up logging
    log_file = args.log_file or os.path.join(args.output_dir, "analysis.log")
    setup_logging(log_file)
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # First run: analyze dataset and create database
    logging.info("Running initial analysis to create database...")
    analyze_gdelt_dataset(
        args.dataset_dir,
        args.output_dir,
        enable_sentiment=not args.no_sentiment,
        enable_topics=not args.no_topics,
        enable_entities=not args.no_entities,
        enable_database=not args.no_database,
        enable_timelines=False,  # Don't generate timelines yet
        db_path=args.db_path
    )
    
    # Get database path
    db_path = args.db_path or os.path.join(args.output_dir, "gdelt_news.db")
    
    # Get top entities
    logging.info(f"Getting top {args.top_entities} entities from database...")
    top_entities = get_top_entities(db_path, limit=args.top_entities, min_mentions=args.min_mentions)
    logging.info(f"Found {len(top_entities)} entities")
    
    # Process entities in batches
    for i in range(0, len(top_entities), args.batch_size):
        batch = top_entities[i:i+args.batch_size]
        batch_num = i // args.batch_size + 1
        batch_output_dir = os.path.join(args.output_dir, f"batch_{batch_num}")
        
        logging.info(f"Processing batch {batch_num} with {len(batch)} entities: {', '.join(batch)}")
        
        # Run analysis for this batch
        analyze_gdelt_dataset(
            args.dataset_dir,
            batch_output_dir,
            enable_sentiment=not args.no_sentiment,
            enable_topics=False,  # Skip topic modeling for batches
            enable_entities=False,  # Skip entity extraction for batches
            enable_database=True,
            enable_timelines=True,
            enable_event_sentiment=True,
            enable_cross_entity=True,
            enable_predictions=True,
            db_path=db_path,  # Use the same database
            timeline_entities=batch
        )
    
    logging.info(f"Analysis complete! Results saved to {args.output_dir}")

if __name__ == "__main__":
    main()
