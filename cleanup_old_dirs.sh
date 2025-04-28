#!/bin/bash
# Script to safely remove old analysis and dataset directories

# Define directories to keep
KEEP_DIRS=(
  "analysis_gdelt_chunks"
  "dataset_gdelt_enhanced"
)

# Remove old analysis directories
echo "Removing old analysis directories..."
for dir in analysis_*; do
  # Skip directories we want to keep
  if [[ " ${KEEP_DIRS[@]} " =~ " ${dir} " ]]; then
    echo "  Keeping $dir"
    continue
  fi
  
  echo "  Removing $dir"
  rm -rf "$dir"
done

# Remove old dataset directories
echo "Removing old dataset directories..."
for dir in dataset_*; do
  # Skip directories we want to keep
  if [[ " ${KEEP_DIRS[@]} " =~ " ${dir} " ]]; then
    echo "  Keeping $dir"
    continue
  fi
  
  echo "  Removing $dir"
  rm -rf "$dir"
done

echo "Cleanup complete!"
