#!/bin/bash

# Run all tests for Hydra News
# This script runs unit tests and integration tests

# Set colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Error handling
set -e

echo -e "${YELLOW}Starting Hydra News test suite...${NC}"
echo "------------------------------------------------"

# Go to project root
cd "$(dirname "$0")/.."
PROJECT_ROOT=$(pwd)
echo ${YELLOW}Project root: $PROJECT_ROOT${NC}
echo "------------------------------------------------"

# Run Go unit tests
cd "$PROJECT_ROOT/go"
echo -e "${YELLOW}Running Go unit tests...${NC}"
go test -v ./... || { echo -e "${RED}Go unit tests failed${NC}"; exit 1; }
echo -e "${GREEN}Go unit tests passed${NC}"
echo "------------------------------------------------"
cd "$PROJECT_ROOT"

# Run Python unit tests
echo -e "${YELLOW}Running Python unit tests...${NC}"
cd "$PROJECT_ROOT/python"
python -m unittest discover -s ../tests/unit/python || { echo -e "${RED}Python unit tests failed${NC}"; exit 1; }
echo -e "${GREEN}Python unit tests passed${NC}"
echo "------------------------------------------------"

# Run integration tests
echo -e "${YELLOW}Running integration tests...${NC}"
cd "$PROJECT_ROOT/tests/integration"
python test_api_content_processing.py || { echo -e "${RED}Integration tests failed${NC}"; exit 1; }
echo -e "${GREEN}Integration tests passed${NC}"
echo "------------------------------------------------"

# Run security tests
echo -e "${YELLOW}Running security tests...${NC}"
cd "$PROJECT_ROOT/tests"
./test_anonymity || { echo -e "${RED}Security tests failed${NC}"; exit 1; }
echo -e "${GREEN}Security tests passed${NC}"
echo "------------------------------------------------"

echo -e "${GREEN}All tests passed successfully!${NC}"
exit 0
