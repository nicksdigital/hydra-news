#!/usr/bin/env python3
"""
GDELT Analyzer CLI

This script provides a command-line interface for analyzing GDELT news data.
"""

import os
import sys
import argparse
from python.src.gdelt.analyzer.core import analyze_gdelt_dataset, setup_logging

def main():
    """Main entry point"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Analyze GDELT news dataset")
    parser.add_argument("--dataset-dir", default="dataset_gdelt_month", help="Directory containing the dataset")
    parser.add_argument("--output-dir", default="analysis_gdelt", help="Directory to save the analysis results")
    parser.add_argument("--log-file", default=None, help="Path to log file")
    parser.add_argument("--no-sentiment", action="store_true", help="Disable sentiment analysis")
    parser.add_argument("--no-topics", action="store_true", help="Disable topic modeling")
    parser.add_argument("--n-topics", type=int, default=10, help="Number of topics for topic modeling")
    parser.add_argument("--split-chunks", action="store_true", help="Split dataset into chunks")
    parser.add_argument("--chunk-size", type=int, default=1000, help="Number of articles per chunk")
    parser.add_argument("--no-entities", action="store_true", help="Disable entity extraction")
    parser.add_argument("--no-database", action="store_true", help="Disable database storage")
    parser.add_argument("--enable-timelines", action="store_true", help="Enable timeline generation")
    parser.add_argument("--enable-event-sentiment", action="store_true", help="Enable sentiment analysis by event")
    parser.add_argument("--enable-cross-entity", action="store_true", help="Enable cross-entity event analysis")
    parser.add_argument("--enable-predictions", action="store_true", help="Enable predictive event detection")
    parser.add_argument("--timeline-entities", nargs="+", help="Entities to generate timelines for")
    parser.add_argument("--db-path", default=None, help="Path to the SQLite database file")
    args = parser.parse_args()

    # Set up logging
    log_file = args.log_file or os.path.join(args.output_dir, "analysis.log")
    setup_logging(log_file)

    # Run analysis
    analyze_gdelt_dataset(
        args.dataset_dir,
        args.output_dir,
        enable_sentiment=not args.no_sentiment,
        enable_topics=not args.no_topics,
        enable_entities=not args.no_entities,
        enable_database=not args.no_database,
        enable_timelines=args.enable_timelines,
        enable_event_sentiment=args.enable_event_sentiment,
        enable_cross_entity=args.enable_cross_entity,
        enable_predictions=args.enable_predictions,
        db_path=args.db_path,
        n_topics=args.n_topics,
        timeline_entities=args.timeline_entities
    )

    # Split dataset into chunks if requested
    if args.split_chunks:
        from python.src.gdelt.analyzer.data_loader import load_dataset, split_dataset_into_chunks

        # Load the dataset
        articles, _, _ = load_dataset(args.dataset_dir)

        # Split into chunks
        chunk_paths = split_dataset_into_chunks(
            articles,
            chunk_size=args.chunk_size,
            output_dir=os.path.join(args.output_dir, "chunks")
        )

        print(f"Split dataset into {len(chunk_paths)} chunks")

if __name__ == "__main__":
    main()
