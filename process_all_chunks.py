#!/usr/bin/env python3
"""
Process all chunks with a delay between them
"""

import os
import time
import argparse
import subprocess
import logging
import json
from glob import glob
from python.src.gdelt.config.database_config import get_database_config

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def process_all_chunks(chunks_dir, config_path=None, output_dir=None, process_script=None, delay=10, limit=None):
    """
    Process all chunks with a delay between them

    Args:
        chunks_dir: Directory containing chunk files
        config_path: Path to database configuration file
        output_dir: Directory to save output files
        process_script: Path to the script for processing chunks
        delay: Delay in seconds between processing chunks
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

    # Process each chunk
    for i, chunk_path in enumerate(chunk_files):
        chunk_name = os.path.basename(chunk_path)
        logger.info(f"Processing chunk {i+1}/{len(chunk_files)}: {chunk_name}")

        # Process the chunk
        cmd = [
            'python', '-m', 'python.src.gdelt.analyzer.process_chunk',
            '--chunk-path', chunk_path,
            '--output-dir', output_dir
        ]

        # Add database configuration
        if db_config['use_postgres']:
            cmd.extend(['--use-postgres', 'true'])
            # Add PostgreSQL configuration
            cmd.extend(['--postgres-host', db_config['postgres']['host']])
            cmd.extend(['--postgres-port', str(db_config['postgres']['port'])])
            cmd.extend(['--postgres-db', db_config['postgres']['dbname']])
            cmd.extend(['--postgres-user', db_config['postgres']['user']])
            cmd.extend(['--postgres-password', db_config['postgres']['password']])
        else:
            cmd.extend(['--use-postgres', 'false'])
            cmd.extend(['--db-path', db_config['sqlite']['db_path']])

        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()

        if process.returncode == 0:
            logger.info(f"Successfully processed chunk: {chunk_name}")
        else:
            logger.error(f"Error processing chunk {chunk_name}: {stderr.decode()}")

        # Wait before processing the next chunk
        if i < len(chunk_files) - 1:
            logger.info(f"Waiting {delay} seconds before processing the next chunk...")
            time.sleep(delay)

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Process all chunks with a delay')
    parser.add_argument('--chunks-dir', type=str, default='analysis_gdelt_chunks/chunks',
                        help='Directory containing chunk files')
    parser.add_argument('--config-path', type=str, default='config/database.json',
                        help='Path to database configuration file')
    parser.add_argument('--output-dir', type=str, default='analysis_gdelt_chunks',
                        help='Directory to save output files')
    parser.add_argument('--process-script', type=str,
                        default='python/src/gdelt/analyzer/process_chunk.py',
                        help='Path to the script for processing chunks')
    parser.add_argument('--delay', type=int, default=10,
                        help='Delay in seconds between processing chunks')
    parser.add_argument('--limit', type=int, default=None,
                        help='Maximum number of chunks to process')
    args = parser.parse_args()

    process_all_chunks(args.chunks_dir, args.config_path, args.output_dir,
                      args.process_script, args.delay, args.limit)

if __name__ == '__main__':
    main()
