#!/bin/bash
# Test runner for Hydra News Go components

# Set up error handling
set -e
set -o pipefail

# Change to the go directory
cd "$(dirname "$0")"

# Run all tests
echo "Running Go tests..."
go test -v ./...

# Run specific tests if requested
if [ "$1" != "" ]; then
    echo "Running tests matching pattern: $1"
    go test -v ./... -run "$1"
fi

echo "All tests completed successfully!"
