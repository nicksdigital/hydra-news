#!/usr/bin/env python3
"""
Run Full GDELT Analysis Pipeline

This script runs the full GDELT analysis pipeline:
1. Fetch data
2. Analyze data
3. Run event detection
4. Start dashboard
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
    parser = argparse.ArgumentParser(description='Run Full GDELT Analysis Pipeline')
    
    # Data fetching options
    parser.add_argument('--fetch-data', action='store_true',
                        help='Fetch new data from GDELT')
    parser.add_argument('--dataset-dir', type=str, default='dataset_gdelt_enhanced',
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
    
    # Event detection options
    parser.add_argument('--detect-events', action='store_true',
                        help='Run event detection')
    parser.add_argument('--all-analyses', action='store_true',
                        help='Run all types of event analyses')
    parser.add_argument('--days-back', type=int, default=30,
                        help='Number of days to look back for event detection')
    
    # Prediction options
    parser.add_argument('--predict', action='store_true',
                        help='Run prediction models')
    parser.add_argument('--days-to-predict', type=int, default=14,
                        help='Number of days to predict into the future')
    
    # Dashboard options
    parser.add_argument('--start-dashboard', action='store_true',
                        help='Start the dashboard after analysis')
    parser.add_argument('--port', type=int, default=5000,
                        help='Port for the dashboard')
    parser.add_argument('--no-browser', action='store_true',
                        help='Do not open browser automatically')
    
    # Run all steps
    parser.add_argument('--run-all', action='store_true',
                        help='Run all steps in the pipeline')
    
    return parser.parse_args()

def run_fetch_data(args):
    """Run the enhanced data fetcher"""
    logger.info("Running enhanced data fetcher...")
    
    # Build command
    cmd = [
        sys.executable, 
        '-m',
        'python.src.gdelt.fetch_gdelt_enhanced',
        '--output-dir', args.dataset_dir,
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
        '-m',
        'python.src.gdelt.analyze_gdelt_all_entities',
        '--dataset-dir', args.dataset_dir,
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

def run_event_detection(args):
    """Run advanced event detection"""
    logger.info("Running advanced event detection...")
    
    # Build command
    cmd = [
        sys.executable, 
        '-m',
        'python.src.gdelt.run_advanced_event_detection',
        '--db-path', os.path.join(args.analysis_dir, 'gdelt_news.db'),
        '--output-dir', os.path.join(args.analysis_dir, 'events'),
        '--top-entities', str(args.top_entities),
        '--min-mentions', str(args.min_mentions),
        '--days-back', str(args.days_back)
    ]
    
    if args.all_analyses:
        cmd.append('--all-analyses')
    else:
        cmd.extend(['--entity-events', '--correlated-events'])
    
    # Run command
    logger.info(f"Running command: {' '.join(cmd)}")
    
    try:
        subprocess.run(cmd, check=True)
        logger.info("Event detection completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running event detection: {e}")
        return False

def run_prediction(args):
    """Run prediction models"""
    logger.info("Running prediction models...")
    
    # Build command
    cmd = [
        sys.executable, 
        '-m',
        'python.src.gdelt.run_enhanced_analysis',
        '--predict',
        '--analysis-dir', args.analysis_dir,
        '--days-to-predict', str(args.days_to_predict),
        '--top-entities', str(args.top_entities)
    ]
    
    # Run command
    logger.info(f"Running command: {' '.join(cmd)}")
    
    try:
        subprocess.run(cmd, check=True)
        logger.info("Prediction completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running prediction: {e}")
        return False

def start_dashboard(args):
    """Start the dashboard"""
    logger.info("Starting dashboard...")
    
    # Build command
    cmd = [
        sys.executable, 
        '-m',
        'python.src.gdelt.run_dashboard',
        '--port', str(args.port),
        '--db-path', os.path.join(args.analysis_dir, 'gdelt_news.db')
    ]
    
    if args.no_browser:
        cmd.append('--no-browser')
    
    # Run command
    logger.info(f"Running command: {' '.join(cmd)}")
    
    try:
        # Run in a new process and don't wait
        process = subprocess.Popen(cmd)
        logger.info(f"Dashboard started on port {args.port}")
        return True
    except Exception as e:
        logger.error(f"Error starting dashboard: {e}")
        return False

def main():
    """Main entry point"""
    args = parse_args()
    
    # Record start time
    start_time = time.time()
    
    # If run-all is specified, set all steps to True
    if args.run_all:
        args.fetch_data = True
        args.analyze_data = True
        args.detect_events = True
        args.predict = True
        args.start_dashboard = True
        args.all_analyses = True
    
    # Create output directories
    if args.fetch_data:
        os.makedirs(args.dataset_dir, exist_ok=True)
    
    if args.analyze_data or args.detect_events or args.predict:
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
    
    # Run event detection
    if args.detect_events:
        if not run_event_detection(args):
            logger.error("Event detection failed")
            # Continue with other steps
    
    # Run prediction models
    if args.predict:
        if not run_prediction(args):
            logger.error("Prediction failed")
            # Continue with other steps
    
    # Start dashboard
    if args.start_dashboard:
        if not start_dashboard(args):
            logger.error("Failed to start dashboard")
            return 1
    
    # Record end time
    end_time = time.time()
    elapsed_time = end_time - start_time
    
    logger.info(f"Pipeline completed successfully in {elapsed_time:.2f} seconds")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
