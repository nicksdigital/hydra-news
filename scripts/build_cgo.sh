#!/bin/bash
# Comprehensive build script for Hydra News with CGO

set -e  # Exit on any error

# Directory paths
PROJECT_ROOT=$(pwd)
C_DIR="$PROJECT_ROOT/c"
GO_DIR="$PROJECT_ROOT/go"
LIB_DIR="$C_DIR/lib"
BUILD_DIR="$C_DIR/build"
INCLUDE_DIR="$C_DIR/include"

# Create necessary directories
mkdir -p "$LIB_DIR" "$BUILD_DIR" "$INCLUDE_DIR" "$PROJECT_ROOT/bin"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}Building Hydra News with CGO...${NC}"

# Step 1: Build C libraries
echo -e "${BLUE}Step 1: Building C libraries...${NC}"

# First, compile the individual C components
cd "$C_DIR"

# Compile QZKP
echo -e "${YELLOW}Compiling quantum_zkp.c${NC}"
gcc -Wall -Wextra -fPIC -O2 -Isrc -c src/quantum_zkp.c -o $BUILD_DIR/quantum_zkp.o
if [ $? -ne 0 ]; then
  echo -e "${RED}Failed to compile quantum_zkp.c${NC}"
  exit 1
fi
cp src/quantum_zkp.h $INCLUDE_DIR/

# Compile logical entanglement
echo -e "${YELLOW}Compiling logical_entanglement.c${NC}"
gcc -Wall -Wextra -fPIC -O2 -Isrc -c src/logical_entanglement.c -o $BUILD_DIR/logical_entanglement.o
if [ $? -ne 0 ]; then
  echo -e "${RED}Failed to compile logical_entanglement.c${NC}"
  exit 1
fi
cp src/logical_entanglement.h $INCLUDE_DIR/

# Compile Kyber
echo -e "${YELLOW}Compiling kyber.c${NC}"
gcc -Wall -Wextra -fPIC -O2 -Isrc -c src/postquantum/kyber.c -o $BUILD_DIR/kyber.o
if [ $? -ne 0 ]; then
  echo -e "${RED}Failed to compile kyber.c${NC}"
  exit 1
fi
cp src/postquantum/kyber.h $INCLUDE_DIR/

# Compile Falcon
echo -e "${YELLOW}Compiling falcon.c${NC}"
gcc -Wall -Wextra -fPIC -O2 -Isrc -c src/postquantum/falcon.c -o $BUILD_DIR/falcon.o
if [ $? -ne 0 ]; then
  echo -e "${RED}Failed to compile falcon.c${NC}"
  exit 1
fi
cp src/postquantum/falcon.h $INCLUDE_DIR/

# Compile crypto adapter
echo -e "${YELLOW}Compiling crypto_adapter.c${NC}"
gcc -Wall -Wextra -fPIC -O2 -Isrc -c src/postquantum/crypto_adapter.c -o $BUILD_DIR/crypto_adapter.o
if [ $? -ne 0 ]; then
  echo -e "${RED}Failed to compile crypto_adapter.c${NC}"
  exit 1
fi
cp src/postquantum/crypto_adapter.h $INCLUDE_DIR/

# Create shared libraries
echo -e "${YELLOW}Creating shared libraries...${NC}"

# QZKP library
gcc -shared -o $LIB_DIR/libqzkp.so $BUILD_DIR/quantum_zkp.o -lcrypto -lssl
if [ $? -ne 0 ]; then
  echo -e "${RED}Failed to create QZKP library${NC}"
  exit 1
fi

# Logical entanglement library
gcc -shared -o $LIB_DIR/lible.so $BUILD_DIR/logical_entanglement.o -lcrypto -lssl
if [ $? -ne 0 ]; then
  echo -e "${RED}Failed to create logical entanglement library${NC}"
  exit 1
fi

# Kyber library
gcc -shared -o $LIB_DIR/libkyber.so $BUILD_DIR/kyber.o -lcrypto -lssl
if [ $? -ne 0 ]; then
  echo -e "${RED}Failed to create Kyber library${NC}"
  exit 1
fi

# Falcon library
gcc -shared -o $LIB_DIR/libfalcon.so $BUILD_DIR/falcon.o -lcrypto -lssl
if [ $? -ne 0 ]; then
  echo -e "${RED}Failed to create Falcon library${NC}"
  exit 1
fi

# Crypto adapter library
gcc -shared -o $LIB_DIR/libcryptoadapter.so $BUILD_DIR/crypto_adapter.o -L$LIB_DIR -lqzkp -lkyber -lfalcon -lcrypto -lssl
if [ $? -ne 0 ]; then
  echo -e "${RED}Failed to create crypto adapter library${NC}"
  exit 1
fi

echo -e "${GREEN}All C libraries built successfully.${NC}"

# Step 2: Set up environment variables for CGO
echo -e "${BLUE}Step 2: Setting up CGO environment variables...${NC}"

export LD_LIBRARY_PATH="$LIB_DIR:$LD_LIBRARY_PATH"
export CGO_ENABLED=1
export CGO_CFLAGS="-I$INCLUDE_DIR"
export CGO_LDFLAGS="-L$LIB_DIR -lqzkp -lkyber -lfalcon -lcryptoadapter -lcrypto -lssl"

# Save environment to a file for later use
cat > "$PROJECT_ROOT/scripts/cgo_env.sh" << EOF
#!/bin/bash
# Environment settings for Hydra News CGO
export CGO_ENABLED=1 
export LD_LIBRARY_PATH="$LIB_DIR:\$LD_LIBRARY_PATH"
export CGO_CFLAGS="-I$INCLUDE_DIR"
export CGO_LDFLAGS="-L$LIB_DIR -lqzkp -lkyber -lfalcon -lcryptoadapter -lcrypto -lssl"
EOF

chmod +x "$PROJECT_ROOT/scripts/cgo_env.sh"
echo -e "${GREEN}Environment variables saved to $PROJECT_ROOT/scripts/cgo_env.sh${NC}"

# Step 3: Build Go code with CGO
echo -e "${BLUE}Step 3: Building Go code with CGO...${NC}"

cd "$GO_DIR"
echo -e "${YELLOW}Building Go code...${NC}"

# Move mock implementations if they exist
if [ -f "$GO_DIR/identity/mock_crypto.go" ]; then
  mv "$GO_DIR/identity/mock_crypto.go" "$GO_DIR/identity/mock_crypto.go.bak"
  echo -e "${YELLOW}Backed up mock_crypto.go${NC}"
fi

if [ -f "$GO_DIR/keyvault/mock_pq_crypto.go" ]; then
  mv "$GO_DIR/keyvault/mock_pq_crypto.go" "$GO_DIR/keyvault/mock_pq_crypto.go.bak"
  echo -e "${YELLOW}Backed up mock_pq_crypto.go${NC}"
fi

# Build the Go code 
go build -v -o "$PROJECT_ROOT/bin/hydra-news" .
if [ $? -ne 0 ]; then
  echo -e "${RED}Failed to build Go code${NC}"
  exit 1
fi

echo -e "${GREEN}Go code built successfully.${NC}"

# Step 4: Run tests
echo -e "${BLUE}Step 4: Running tests...${NC}"

cd "$GO_DIR"
echo -e "${YELLOW}Running identity package tests...${NC}"
go test -v ./identity

if [ $? -ne 0 ]; then
  echo -e "${RED}Identity tests failed${NC}"
  exit 1
fi

echo -e "${YELLOW}Running keyvault package tests...${NC}"
go test -v ./keyvault

if [ $? -ne 0 ]; then
  echo -e "${RED}Keyvault tests failed${NC}"
  exit 1
fi

echo -e "${GREEN}All tests passed!${NC}"
echo -e "${GREEN}Build completed successfully!${NC}"
echo -e "${YELLOW}To run Hydra News, use:${NC}"
echo -e "${YELLOW}source $PROJECT_ROOT/scripts/cgo_env.sh && $PROJECT_ROOT/bin/hydra-news${NC}"
