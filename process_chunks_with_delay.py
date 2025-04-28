#!/usr/bin/env python3
"""
Process chunks one by one with a delay between them
"""

import os
import time
import argparse
import subprocess
import logging
from glob import glob

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def process_chunks(chunks_dir, db_path, output_dir, process_script, delay=10):
    """
    Process chunks one by one with a delay between them
    
    Args:
        chunks_dir: Directory containing chunk files
        db_path: Path to the database file
        output_dir: Directory to save output files
        process_script: Path to the script for processing chunks
        delay: Delay in seconds between processing chunks
    """
    # Get list of chunk files
    chunk_files = sorted(glob(os.path.join(chunks_dir, "*.csv")))
    
    if not chunk_files:
        logger.info("No chunk files found")
        return
    
    logger.info(f"Found {len(chunk_files)} chunk files")
    
    # Process each chunk
    for i, chunk_path in enumerate(chunk_files):
        chunk_name = os.path.basename(chunk_path)
        logger.info(f"Processing chunk {i+1}/{len(chunk_files)}: {chunk_name}")
        
        # Process the chunk
        cmd = [
            'python', process_script,
            '--chunk-path', chunk_path,
            '--db-path', db_path,
            '--output-dir', output_dir
        ]
        
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
    parser = argparse.ArgumentParser(description='Process chunks one by one with a delay')
    parser.add_argument('--chunks-dir', type=str, default='analysis_gdelt_chunks/chunks',
                        help='Directory containing chunk files')
    parser.add_argument('--db-path', type=str, default='analysis_gdelt_chunks/gdelt_news.db',
                        help='Path to the database file')
    parser.add_argument('--output-dir', type=str, default='analysis_gdelt_chunks',
                        help='Directory to save output files')
    parser.add_argument('--process-script', type=str, 
                        default='python/src/gdelt/analyzer/process_chunk.py',
                        help='Path to the script for processing chunks')
    parser.add_argument('--delay', type=int, default=10,
                        help='Delay in seconds between processing chunks')
    args = parser.parse_args()
    
    process_chunks(args.chunks_dir, args.db_path, args.output_dir, args.process_script, args.delay)

if __name__ == '__main__':
    main()
