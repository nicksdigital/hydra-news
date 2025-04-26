#!/bin/bash
# Script to run integration tests for Hydra News CGO bindings

set -e  # Exit on any error

# Directory paths
ROOT_DIR=$(pwd)
C_DIR="$ROOT_DIR/c"
GO_DIR="$ROOT_DIR/go"
LIB_DIR="$C_DIR/lib"
INCLUDE_DIR="$C_DIR/include"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Running integration tests for Hydra News...${NC}"

# Check if C libraries have been built
if [ ! -f "$LIB_DIR/libqzkp.so" ] || [ ! -f "$LIB_DIR/libkyber.so" ] || [ ! -f "$LIB_DIR/libfalcon.so" ] || [ ! -f "$LIB_DIR/libcryptoadapter.so" ]; then
    echo -e "${YELLOW}C libraries not found. Building them first...${NC}"
    bash "$ROOT_DIR/scripts/build_c_libs.sh"
fi

# Source environment settings
source "$ROOT_DIR/scripts/c_lib_env.sh"

echo -e "${GREEN}Running CGO bindings tests...${NC}"

# Go to Go directory and run the identity tests
cd "$GO_DIR"
echo -e "${YELLOW}Testing identity package...${NC}"
CGO_ENABLED=1 go test -v ./identity

# Run the keyvault tests
echo -e "${YELLOW}Testing keyvault package...${NC}"
CGO_ENABLED=1 go test -v ./keyvault

echo -e "${GREEN}All integration tests completed.${NC}"
