#!/usr/bin/env python3
"""
Process all chunks immediately and store them in the PostgreSQL database
"""

import os
import sys
import logging
import argparse
import subprocess
import concurrent.futures
from glob import glob
from tqdm import tqdm
from python.src.gdelt.config.database_config import get_database_config

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def process_chunk(chunk_path, db_config, output_dir):
    """
    Process a single chunk
    
    Args:
        chunk_path: Path to the chunk file
        db_config: Database configuration
        output_dir: Directory to save output files
        
    Returns:
        True if successful, False otherwise
    """
    chunk_name = os.path.basename(chunk_path)
    logger.info(f"Processing chunk: {chunk_name}")
    
    # Process the chunk
    cmd = [
        'python', '-m', 'python.src.gdelt.analyzer.process_chunk_postgres',
        '--chunk-path', chunk_path,
        '--output-dir', output_dir,
        '--postgres-host', db_config['postgres']['host'],
        '--postgres-port', str(db_config['postgres']['port']),
        '--postgres-db', db_config['postgres']['dbname'],
        '--postgres-user', db_config['postgres']['user'],
        '--postgres-password', db_config['postgres']['password']
    ]
    
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    
    if process.returncode == 0:
        logger.info(f"Successfully processed chunk: {chunk_name}")
        return True
    else:
        logger.error(f"Error processing chunk {chunk_name}: {stderr.decode()}")
        return False

def process_all_chunks(chunks_dir, config_path=None, output_dir=None, workers=4, limit=None):
    """
    Process all chunks in parallel
    
    Args:
        chunks_dir: Directory containing chunk files
        config_path: Path to database configuration file
        output_dir: Directory to save output files
        workers: Number of worker processes
        limit: Maximum number of chunks to process (None for all)
    """
    # Get database configuration
    db_config = get_database_config(config_path)
    
    # Get list of chunk files
    chunk_files = sorted(glob(os.path.join(chunks_dir, "*.csv")))
    
    if not chunk_files:
        logger.info("No chunk files found")
        return
    
    # Apply limit if specified
    if limit is not None and limit > 0:
        chunk_files = chunk_files[:limit]
    
    logger.info(f"Found {len(chunk_files)} chunk files, will process {len(chunk_files)} chunks")
    
    # Process chunks in parallel
    success_count = 0
    error_count = 0
    
    with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(process_chunk, chunk_path, db_config, output_dir): chunk_path
            for chunk_path in chunk_files
        }
        
        for future in tqdm(concurrent.futures.as_completed(futures), total=len(futures), desc="Processing chunks"):
            chunk_path = futures[future]
            chunk_name = os.path.basename(chunk_path)
            
            try:
                success = future.result()
                if success:
                    success_count += 1
                else:
                    error_count += 1
            except Exception as e:
                logger.error(f"Exception processing chunk {chunk_name}: {e}")
                error_count += 1
    
    logger.info(f"Processing completed: {success_count} successful, {error_count} errors")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Process all chunks immediately')
    parser.add_argument('--chunks-dir', type=str, default='analysis_gdelt_chunks/chunks',
                        help='Directory containing chunk files')
    parser.add_argument('--config-path', type=str, default='config/database.json',
                        help='Path to database configuration file')
    parser.add_argument('--output-dir', type=str, default='analysis_gdelt_chunks',
                        help='Directory to save output files')
    parser.add_argument('--workers', type=int, default=4,
                        help='Number of worker processes')
    parser.add_argument('--limit', type=int, default=None,
                        help='Maximum number of chunks to process')
    args = parser.parse_args()
    
    process_all_chunks(args.chunks_dir, args.config_path, args.output_dir, args.workers, args.limit)

if __name__ == '__main__':
    main()
