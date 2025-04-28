#!/usr/bin/env python3
"""
Monitor the chunks directory and process new chunks as they arrive
"""

import os
import time
import sqlite3
import logging
import argparse
import subprocess
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ChunkHandler(FileSystemEventHandler):
    """Handler for chunk file events"""
    
    def __init__(self, db_path, output_dir, process_script):
        """
        Initialize the chunk handler
        
        Args:
            db_path: Path to the database file
            output_dir: Directory to save output files
            process_script: Path to the script for processing chunks
        """
        self.db_path = db_path
        self.output_dir = output_dir
        self.process_script = process_script
        self.processing = False
    
    def on_created(self, event):
        """Handle file creation events"""
        if event.is_directory:
            return
            
        # Check if it's a CSV file
        if not event.src_path.endswith('.csv'):
            return
            
        # Check if it's a chunk file
        if 'chunk' not in os.path.basename(event.src_path):
            return
            
        logger.info(f"New chunk detected: {event.src_path}")
        self.process_chunk(event.src_path)
    
    def process_chunk(self, chunk_path):
        """
        Process a chunk file
        
        Args:
            chunk_path: Path to the chunk file
        """
        if self.processing:
            logger.info(f"Already processing a chunk. Will process {chunk_path} later.")
            return
            
        self.processing = True
        try:
            # Check if chunk has already been processed
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            chunk_name = os.path.basename(chunk_path)
            
            cursor.execute('SELECT status FROM processed_chunks WHERE chunk_name = ?', (chunk_name,))
            result = cursor.fetchone()
            
            if result and result[0] == 'completed':
                logger.info(f"Chunk {chunk_name} has already been processed. Skipping.")
                conn.close()
                self.processing = False
                return
                
            conn.close()
            
            # Process the chunk
            logger.info(f"Processing chunk: {chunk_path}")
            cmd = [
                'python', self.process_script,
                '--chunk-path', chunk_path,
                '--db-path', self.db_path,
                '--output-dir', self.output_dir
            ]
            
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()
            
            if process.returncode == 0:
                logger.info(f"Successfully processed chunk: {chunk_name}")
            else:
                logger.error(f"Error processing chunk {chunk_name}: {stderr.decode()}")
                
        except Exception as e:
            logger.error(f"Error processing chunk {chunk_path}: {e}")
        finally:
            self.processing = False

def process_existing_chunks(chunks_dir, handler):
    """
    Process existing chunks in the directory
    
    Args:
        chunks_dir: Directory containing chunk files
        handler: ChunkHandler instance
    """
    logger.info(f"Checking for existing chunks in {chunks_dir}")
    
    # Get list of CSV files in the directory
    chunk_files = [f for f in os.listdir(chunks_dir) if f.endswith('.csv') and 'chunk' in f]
    
    if not chunk_files:
        logger.info("No existing chunks found")
        return
        
    logger.info(f"Found {len(chunk_files)} existing chunks")
    
    # Process each chunk
    for chunk_file in sorted(chunk_files):
        chunk_path = os.path.join(chunks_dir, chunk_file)
        handler.process_chunk(chunk_path)

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Monitor chunks directory and process new chunks')
    parser.add_argument('--chunks-dir', type=str, default='analysis_gdelt_chunks/chunks',
                        help='Directory containing chunk files')
    parser.add_argument('--db-path', type=str, default='analysis_gdelt_chunks/gdelt_news.db',
                        help='Path to the database file')
    parser.add_argument('--output-dir', type=str, default='analysis_gdelt_chunks',
                        help='Directory to save output files')
    parser.add_argument('--process-script', type=str, 
                        default='python/src/gdelt/analyzer/process_chunk.py',
                        help='Path to the script for processing chunks')
    args = parser.parse_args()
    
    # Create directories if they don't exist
    os.makedirs(args.chunks_dir, exist_ok=True)
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Create handler
    handler = ChunkHandler(args.db_path, args.output_dir, args.process_script)
    
    # Process existing chunks
    process_existing_chunks(args.chunks_dir, handler)
    
    # Set up observer
    observer = Observer()
    observer.schedule(handler, args.chunks_dir, recursive=False)
    observer.start()
    
    logger.info(f"Monitoring {args.chunks_dir} for new chunks")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    
    observer.join()

if __name__ == '__main__':
    main()
