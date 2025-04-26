#!/bin/bash
# Script to build Hydra News with CGO integration and run the demo

set -e  # Exit on any error

# Directory paths
ROOT_DIR=$(pwd)
C_DIR="$ROOT_DIR/c"
GO_DIR="$ROOT_DIR/go"
EXAMPLES_DIR="$ROOT_DIR/examples"
SCRIPTS_DIR="$ROOT_DIR/scripts"
BIN_DIR="$ROOT_DIR/bin"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}Building Hydra News with CGO integration and running demo...${NC}"

# Create bin directory if it doesn't exist
mkdir -p "$BIN_DIR"

# Step 1: Build C libraries
echo -e "${BLUE}Step 1: Building C libraries...${NC}"

cd "$C_DIR"
make -f Makefile.cgo rebuild

echo -e "${GREEN}C libraries built successfully.${NC}"

# Step 2: Set up environment variables for CGO
echo -e "${BLUE}Step 2: Setting up CGO environment variables...${NC}"

export LD_LIBRARY_PATH="$C_DIR/lib:$LD_LIBRARY_PATH"
export CGO_CFLAGS="-I$C_DIR/include"
export CGO_LDFLAGS="-L$C_DIR/lib -lhydracgo -lcrypto -lssl"

echo "LD_LIBRARY_PATH=$LD_LIBRARY_PATH"
echo "CGO_CFLAGS=$CGO_CFLAGS"
echo "CGO_LDFLAGS=$CGO_LDFLAGS"

# Save environment to a file for later use
cat > "$SCRIPTS_DIR/cgo_env.sh" << EOF
#!/bin/bash
# Environment settings for Hydra News CGO integration
export LD_LIBRARY_PATH="$C_DIR/lib:\$LD_LIBRARY_PATH"
export CGO_CFLAGS="-I$C_DIR/include"
export CGO_LDFLAGS="-L$C_DIR/lib -lhydracgo -lcrypto -lssl"
EOF

chmod +x "$SCRIPTS_DIR/cgo_env.sh"
echo -e "${GREEN}Environment variables saved to $SCRIPTS_DIR/cgo_env.sh${NC}"

# Step 3: Build and run the main Go application
echo -e "${BLUE}Step 3: Building Go application...${NC}"

cd "$GO_DIR"
go build -v -o "$BIN_DIR/hydra-news" .

echo -e "${GREEN}Go code built successfully.${NC}"

# Step 4: Build the demo
echo -e "${BLUE}Step 4: Building the demo application...${NC}"

cd "$EXAMPLES_DIR"
go build -v -o "$BIN_DIR/crypto_demo" .

echo -e "${GREEN}Demo application built successfully.${NC}"

# Step 5: Run the demo
echo -e "${BLUE}Step 5: Running the demo...${NC}"

cd "$ROOT_DIR"
"$BIN_DIR/crypto_demo" --mode=all

echo -e "${GREEN}Demo completed!${NC}"
echo -e "${YELLOW}To run the demo with a specific mode:${NC}"
echo -e "${YELLOW}  $BIN_DIR/crypto_demo --mode=[source|content|channel]${NC}"
