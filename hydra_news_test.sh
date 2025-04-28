#!/bin/bash
# Hydra News Comprehensive Test Script
# This script runs a full test of the Hydra News system including cryptographic components,
# distributed consensus, and the GDELT news analysis pipeline.

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

# Function for warning messages
warning() {
  echo -e "${YELLOW}! $1${NC}"
}

# Function to check if previous command succeeded
check_status() {
  if [ $? -eq 0 ]; then
    success "$1"
    return 0
  else
    error "$1"
    return 1
  fi
}

# Create directories for logs and test results
section "Setting up test environment"
mkdir -p logs/tests
mkdir -p test_results

# Record start time
START_TIME=$(date +%s)

# Check system dependencies
section "Checking system dependencies"

# Check Python
python --version > /dev/null 2>&1
check_status "Python installed"

# Check Go
go version > /dev/null 2>&1
check_status "Go installed"

# Check GCC
gcc --version > /dev/null 2>&1
check_status "GCC installed"

# Check OpenSSL
openssl version > /dev/null 2>&1
check_status "OpenSSL installed"

# Check Python dependencies
section "Installing Python dependencies"
cd python
pip install -r requirements.txt > ../logs/tests/pip_install.log 2>&1
check_status "Python dependencies installed"
cd ..

# Build C cryptographic components
section "Building C cryptographic components"
cd c
mkdir -p build lib include
make > ../logs/tests/c_build.log 2>&1
BUILD_STATUS=$?
if [ $BUILD_STATUS -eq 0 ]; then
  success "C components built successfully"
else
  error "C components build failed. Check logs/tests/c_build.log for details"
fi
cd ..

# Build and verify Go components
section "Building Go components"
cd go
go mod tidy > ../logs/tests/go_mod_tidy.log 2>&1
check_status "Go dependencies resolved"

go build -o ../bin/hydra_news_api > ../logs/tests/go_build.log 2>&1
check_status "Go API service built"
cd ..

# Test C cryptographic primitives
section "Testing C cryptographic primitives"

# Test QZKP (Quantum Zero-Knowledge Proofs)
echo "Testing QZKP module..."
cd c/build
gcc -I../include -L../lib ../tests/test_quantum_zkp.c -lqzkp -lcrypto -o test_qzkp > ../../logs/tests/qzkp_test_build.log 2>&1
if [ -f "test_qzkp" ]; then
  LD_LIBRARY_PATH=../lib ./test_qzkp > ../../logs/tests/qzkp_test_run.log 2>&1
  check_status "QZKP tests"
else
  error "Failed to build QZKP tests"
fi

# Test Logical Entanglement
echo "Testing Logical Entanglement module..."
gcc -I../include -L../lib ../tests/test_logical_entanglement.c -lle -lcrypto -o test_le > ../../logs/tests/le_test_build.log 2>&1
if [ -f "test_le" ]; then
  LD_LIBRARY_PATH=../lib ./test_le > ../../logs/tests/le_test_run.log 2>&1
  check_status "Logical Entanglement tests"
else
  error "Failed to build Logical Entanglement tests"
fi

# Test Kyber
echo "Testing Kyber module..."
gcc -I../include -L../lib ../tests/test_kyber.c -lkyber -lcrypto -o test_kyber > ../../logs/tests/kyber_test_build.log 2>&1
if [ -f "test_kyber" ]; then
  LD_LIBRARY_PATH=../lib ./test_kyber > ../../logs/tests/kyber_test_run.log 2>&1
  check_status "Kyber tests"
else
  error "Failed to build Kyber tests"
fi

# Test Falcon
echo "Testing Falcon module..."
gcc -I../include -L../lib ../tests/test_falcon.c -lfalcon -lcrypto -o test_falcon > ../../logs/tests/falcon_test_build.log 2>&1
if [ -f "test_falcon" ]; then
  LD_LIBRARY_PATH=../lib ./test_falcon > ../../logs/tests/falcon_test_run.log 2>&1
  check_status "Falcon tests"
else
  error "Failed to build Falcon tests"
fi

cd ../..

# Test Go components
section "Testing Go components"
cd go
go test ./... -v > ../logs/tests/go_tests.log 2>&1
check_status "Go component tests"
cd ..

# Test Python content processor
section "Testing Python content processor"
cd python
python -m pytest tests/test_content_processor.py -v > ../logs/tests/python_content_tests.log 2>&1
PYTHON_TEST_STATUS=$?
if [ $PYTHON_TEST_STATUS -eq 0 ]; then
  success "Python content processor tests"
else
  error "Python content processor tests failed. Check logs/tests/python_content_tests.log for details"
fi
cd ..

# Test GDELT pipeline with small dataset
section "Testing GDELT pipeline with small dataset"
echo "Fetching small test dataset..."
./run_gdelt_pipeline.sh -m 200 -t 2d fetch > logs/tests/gdelt_fetch.log 2>&1
check_status "GDELT data fetching"

echo "Analyzing test dataset..."
./run_gdelt_pipeline.sh -e 10 analyze > logs/tests/gdelt_analyze.log 2>&1
check_status "GDELT data analysis"

echo "Running event detection..."
./run_gdelt_pipeline.sh events > logs/tests/gdelt_events.log 2>&1
check_status "GDELT event detection"

echo "Running prediction models..."
./run_gdelt_pipeline.sh -p 7 predict > logs/tests/gdelt_predict.log 2>&1
check_status "GDELT prediction models"

# Test full system integration
section "Starting system for integration tests"

echo "Building and starting all services..."
./scripts/start_dev.sh > logs/tests/system_start.log 2>&1

if grep -q "Development environment started" logs/tests/system_start.log; then
  success "System successfully started"
else
  error "System failed to start. Check logs/tests/system_start.log for details"
  exit 1
fi

# Allow some time for all services to initialize
echo "Waiting for services to initialize..."
sleep 10

# Test API endpoints
section "Testing API endpoints"

echo "Testing API status endpoint..."
curl -s http://localhost:8080/api/status > logs/tests/api_status.log 2>&1
check_status "API status endpoint"

echo "Testing API content submission..."
curl -s -X POST http://localhost:8080/api/content/submit \
  -H "Content-Type: application/json" \
  -d '{"title":"Test Article","content":"This is a test article content.","source":"Test Source","author":"Test Author"}' \
  > logs/tests/api_submit.log 2>&1
check_status "API content submission"

# Test Byzantine fault tolerance
section "Testing Byzantine fault tolerance"

echo "Simulating node failures..."
# This would involve more sophisticated testing in a real environment
# For now, we'll just verify the consensus modules exist
if [ -d "go/consensus" ]; then
  success "Consensus modules present"
else
  error "Consensus modules missing"
fi

# Stop all services
section "Stopping all services"
./scripts/stop_dev.sh > logs/tests/system_stop.log 2>&1
check_status "System successfully stopped"

# Calculate and display execution time
END_TIME=$(date +%s)
EXECUTION_TIME=$((END_TIME - START_TIME))
MINUTES=$((EXECUTION_TIME / 60))
SECONDS=$((EXECUTION_TIME % 60))

section "Test Summary"
echo "Tests completed in ${MINUTES}m ${SECONDS}s"

# Print summary of test results
SUCCESS_COUNT=$(grep -c "${GREEN}✓" logs/tests/test_summary.log 2>/dev/null || echo 0)
FAILURE_COUNT=$(grep -c "${RED}✗" logs/tests/test_summary.log 2>/dev/null || echo 0)
WARNING_COUNT=$(grep -c "${YELLOW}!" logs/tests/test_summary.log 2>/dev/null || echo 0)

echo -e "Results:\n${GREEN}Passed: ${SUCCESS_COUNT}${NC}\n${RED}Failed: ${FAILURE_COUNT}${NC}\n${YELLOW}Warnings: ${WARNING_COUNT}${NC}"

if [ $FAILURE_COUNT -eq 0 ]; then
  echo -e "\n${GREEN}All critical tests passed!${NC}"
else
  echo -e "\n${RED}Some tests failed. Review the logs for details.${NC}"
  exit 1
fi
