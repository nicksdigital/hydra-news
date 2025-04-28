#!/usr/bin/env python3
"""
Split the existing GDELT dataset into smaller chunks of 100 items each
"""

import os
import pandas as pd
import logging
import argparse
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def split_dataset(input_file, output_dir, chunk_size=100):
    """
    Split a dataset into smaller chunks
    
    Args:
        input_file: Path to the input CSV file
        output_dir: Directory to save the chunks
        chunk_size: Number of items per chunk
        
    Returns:
        List of paths to the chunk files
    """
    logger.info(f"Splitting dataset {input_file} into chunks of {chunk_size} items")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Load the dataset
    try:
        df = pd.read_csv(input_file)
        logger.info(f"Loaded dataset with {len(df)} items")
    except Exception as e:
        logger.error(f"Error loading dataset: {e}")
        return []
    
    # Calculate number of chunks
    num_chunks = (len(df) + chunk_size - 1) // chunk_size
    logger.info(f"Will create {num_chunks} chunks")
    
    # Split and save chunks
    chunk_paths = []
    for i in range(num_chunks):
        start_idx = i * chunk_size
        end_idx = min((i + 1) * chunk_size, len(df))
        
        chunk = df.iloc[start_idx:end_idx]
        
        # Create a timestamp to ensure unique filenames
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        chunk_path = os.path.join(output_dir, f"articles_chunk_{i+1:03d}_{timestamp}.csv")
        chunk.to_csv(chunk_path, index=False)
        
        chunk_paths.append(chunk_path)
        logger.info(f"Saved chunk {i+1}/{num_chunks} with {len(chunk)} items to {chunk_path}")
        
    return chunk_paths

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Split dataset into smaller chunks')
    parser.add_argument('--input-file', type=str, required=True,
                        help='Path to the input CSV file')
    parser.add_argument('--output-dir', type=str, default='analysis_gdelt_chunks/chunks',
                        help='Directory to save the chunks')
    parser.add_argument('--chunk-size', type=int, default=100,
                        help='Number of items per chunk')
    args = parser.parse_args()
    
    # Split the dataset
    chunk_paths = split_dataset(args.input_file, args.output_dir, args.chunk_size)
    
    if chunk_paths:
        logger.info(f"Successfully split dataset into {len(chunk_paths)} chunks")
    else:
        logger.error("Failed to split dataset")

if __name__ == '__main__':
    main()
