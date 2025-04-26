#!/bin/bash
# Script to build Hydra News with CGO integration

set -e  # Exit on any error

# Directory paths
ROOT_DIR=$(pwd)
C_DIR="$ROOT_DIR/c"
GO_DIR="$ROOT_DIR/go"
SCRIPTS_DIR="$ROOT_DIR/scripts"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}Building Hydra News with CGO integration...${NC}"

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

# Step 3: Build Go code with CGO
echo -e "${BLUE}Step 3: Building Go code with CGO...${NC}"

cd "$GO_DIR"
go build -v -o "$ROOT_DIR/bin/hydra-news" .

echo -e "${GREEN}Go code built successfully.${NC}"

# Step 4: Run tests
echo -e "${BLUE}Step 4: Running tests...${NC}"

cd "$GO_DIR"
CGO_ENABLED=1 go test -v ./identity ./keyvault

echo -e "${GREEN}Build completed successfully!${NC}"
echo -e "${YELLOW}To run Hydra News, use:${NC}"
echo -e "${YELLOW}source $SCRIPTS_DIR/cgo_env.sh && $ROOT_DIR/bin/hydra-news${NC}"
