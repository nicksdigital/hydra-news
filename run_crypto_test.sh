#!/bin/bash
# Script to compile and run the split cryptographic test

# Set colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print section headers
section() {
  echo -e "\n${BLUE}==== $1 ====${NC}"
}

# Function for success messages
success() {
  echo -e "${GREEN}✓ $1${NC}"
}

# Function for error messages
error() {
  echo -e "${RED}✗ $1${NC}"
}

# Create necessary directories
mkdir -p c/include/postquantum
mkdir -p logs

section "Setting up environment for crypto test"

# First, build the C cryptographic libraries
cd c
echo "Building C cryptographic libraries..."
make > ../logs/c_build.log 2>&1
if [ $? -ne 0 ]; then
  error "Failed to build C libraries. Check logs/c_build.log for details."
  exit 1
fi
success "Built C cryptographic libraries"

# Ensure header files are in the correct locations
echo "Copying header files to include directory..."
cp src/quantum_zkp.h include/
cp src/logical_entanglement.h include/
cp src/postquantum/kyber.h include/postquantum/
cp src/postquantum/falcon.h include/postquantum/
cp src/postquantum/crypto_adapter.h include/postquantum/
success "Copied header files to include directory"
cd ..

section "Compiling Full Cryptographic Test"

# Compile the test program
gcc -I./c/include -L./c/lib crypto_test_main.c -lqzkp -lle -lcrypto -lssl -o crypto_test_executable > logs/crypto_test_compile.log 2>&1

if [ $? -ne 0 ]; then
  error "Failed to compile crypto test. Check logs/crypto_test_compile.log for details."
  cat logs/crypto_test_compile.log
  exit 1
fi

success "Compiled crypto test successfully"

section "Running Full End-to-End Crypto Test"

# Run the test with LD_LIBRARY_PATH set
export LD_LIBRARY_PATH=./c/lib:$LD_LIBRARY_PATH
./crypto_test_executable > logs/crypto_test_run.log 2>&1

if [ $? -ne 0 ]; then
  error "Crypto test failed. Check logs/crypto_test_run.log for details."
  cat logs/crypto_test_run.log
  exit 1
fi

success "Crypto test completed successfully"

# Display the test results
cat logs/crypto_test_run.log

section "Test Summary"

# Count successes and errors
PASSES=$(grep -c "successfully" logs/crypto_test_run.log)
ERRORS=$(grep -c "ERROR\|Failed\|failed" logs/crypto_test_run.log)

echo -e "${GREEN}Passes: $PASSES${NC}"
echo -e "${RED}Errors: $ERRORS${NC}"

if [ $ERRORS -eq 0 ]; then
  echo -e "\n${GREEN}All cryptographic components are working correctly!${NC}"
  echo -e "This confirms that the system can:"
  echo -e "  - Protect source identity and location using zero-knowledge proofs"
  echo -e "  - Create tamper-evident content with logical entanglement"
  echo -e "  - Verify article authenticity with post-quantum signatures"
  echo -e "  - Detect content tampering reliably"
  echo -e "  - Establish secure keys for encrypted content with post-quantum key exchange"
else
  echo -e "\n${RED}Some tests failed - see above for details${NC}"
  exit 1
fi
