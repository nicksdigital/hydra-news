#!/bin/bash
# Script to build C libraries for Hydra News

set -e  # Exit on any error

# Directory paths
ROOT_DIR=$(pwd)
C_DIR="$ROOT_DIR/c"
SRC_DIR="$C_DIR/src"
LIB_DIR="$C_DIR/lib"
INCLUDE_DIR="$C_DIR/include"

# Create directories if they don't exist
mkdir -p "$LIB_DIR"
mkdir -p "$INCLUDE_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Building C libraries for Hydra News...${NC}"

# Check for required tools
if ! command -v gcc &> /dev/null; then
    echo -e "${RED}Error: gcc is not installed. Please install it first.${NC}"
    exit 1
fi

if ! command -v pkg-config &> /dev/null; then
    echo -e "${YELLOW}Warning: pkg-config is not installed. It's recommended for detecting OpenSSL.${NC}"
fi

# Check for OpenSSL
if pkg-config --exists openssl; then
    OPENSSL_CFLAGS=$(pkg-config --cflags openssl)
    OPENSSL_LIBS=$(pkg-config --libs openssl)
else
    echo -e "${YELLOW}Warning: OpenSSL not found via pkg-config. Using default flags.${NC}"
    OPENSSL_CFLAGS="-I/usr/include/openssl"
    OPENSSL_LIBS="-lssl -lcrypto"
fi

# Compile flags
CC=${CC:-gcc}
CFLAGS="-Wall -Wextra -fPIC -O2 -I${SRC_DIR} ${OPENSSL_CFLAGS}"
LDFLAGS="-shared ${OPENSSL_LIBS}"

# Build quantum_zkp library
echo -e "${GREEN}Building quantum_zkp library...${NC}"
$CC $CFLAGS -o "$LIB_DIR/libqzkp.so" "$SRC_DIR/quantum_zkp.c" $LDFLAGS
cp "$SRC_DIR/quantum_zkp.h" "$INCLUDE_DIR/"

# Build kyber library
echo -e "${GREEN}Building kyber library...${NC}"
$CC $CFLAGS -o "$LIB_DIR/libkyber.so" "$SRC_DIR/postquantum/kyber.c" $LDFLAGS
cp "$SRC_DIR/postquantum/kyber.h" "$INCLUDE_DIR/"

# Build falcon library
echo -e "${GREEN}Building falcon library...${NC}"
$CC $CFLAGS -o "$LIB_DIR/libfalcon.so" "$SRC_DIR/postquantum/falcon.c" $LDFLAGS
cp "$SRC_DIR/postquantum/falcon.h" "$INCLUDE_DIR/"

# Build crypto_adapter library
echo -e "${GREEN}Building crypto_adapter library...${NC}"
$CC $CFLAGS -o "$LIB_DIR/libcryptoadapter.so" "$SRC_DIR/postquantum/crypto_adapter.c" $LDFLAGS -L"$LIB_DIR" -lqzkp -lkyber -lfalcon
cp "$SRC_DIR/postquantum/crypto_adapter.h" "$INCLUDE_DIR/"

# Copy logical_entanglement.h (implementation will be added later)
cp "$SRC_DIR/logical_entanglement.h" "$INCLUDE_DIR/"

echo -e "${GREEN}All C libraries built successfully.${NC}"
echo -e "${YELLOW}Make sure to set LD_LIBRARY_PATH to include $LIB_DIR when running Go code.${NC}"
echo -e "${YELLOW}Example: export LD_LIBRARY_PATH=$LIB_DIR:\$LD_LIBRARY_PATH${NC}"

# Create a file with the environment settings
cat > "$ROOT_DIR/scripts/c_lib_env.sh" << EOF
#!/bin/bash
# Environment settings for Hydra News C libraries
export LD_LIBRARY_PATH="$LIB_DIR:\$LD_LIBRARY_PATH"
export CGO_CFLAGS="-I$INCLUDE_DIR"
export CGO_LDFLAGS="-L$LIB_DIR -lqzkp -lkyber -lfalcon -lcryptoadapter"
EOF

chmod +x "$ROOT_DIR/scripts/c_lib_env.sh"
echo -e "${GREEN}Created environment settings script at $ROOT_DIR/scripts/c_lib_env.sh${NC}"
echo -e "${YELLOW}Run 'source $ROOT_DIR/scripts/c_lib_env.sh' before building Go code.${NC}"
