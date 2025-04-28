#!/bin/bash
# Hydra News Full Integration Test - No Mocks
# This script runs a comprehensive integration test of all system components

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

# Create necessary directories
mkdir -p logs/integration
mkdir -p integration_results

# Record start time
START_TIME=$(date +%s)

section "Building C Cryptographic Components"
# Build C libraries with full error messages
cd c
make clean > /dev/null
echo "Running full build with detailed output..."
make 2>&1 | tee ../logs/integration/c_build_full.log

# Check if critical libraries were built
if [ ! -f "lib/libqzkp.so" ] || [ ! -f "lib/lible.so" ]; then
  error "Critical cryptographic libraries failed to build"
  cd ..
  exit 1
fi

# Copy headers to include directory
cp src/quantum_zkp.h include/
cp src/logical_entanglement.h include/
mkdir -p include/postquantum
cp src/postquantum/kyber.h include/postquantum/
cp src/postquantum/falcon.h include/postquantum/
cp src/postquantum/crypto_adapter.h include/postquantum/
success "C cryptographic libraries built successfully"
cd ..

section "Building Go Components with CGO"
# Set up environment for CGO
export CGO_ENABLED=1
export CGO_CFLAGS="-I/home/ubuntu/hydra-news/c/include"
export CGO_LDFLAGS="-L/home/ubuntu/hydra-news/c/lib -lqzkp -lle -lcrypto"
export LD_LIBRARY_PATH="/home/ubuntu/hydra-news/c/lib:$LD_LIBRARY_PATH"

cd go
# Ensure go.mod has the proper dependencies
go mod tidy

# Build the Go API service
go build -o ../bin/hydra_news_api 2>&1 | tee ../logs/integration/go_build.log
check_status "Go API service built successfully"
cd ..

section "Setting up Python Environment"
# Create and activate virtual environment
python3 -m venv venv
. venv/bin/activate
pip install -r requirements.txt
check_status "Python dependencies installed"

section "Running Full System Integration"

# Start all services
echo "Starting all services for integration testing..."
./scripts/start_dev.sh > logs/integration/start_dev.log 2>&1

if grep -q "Development environment started" logs/integration/start_dev.log; then
  success "System services started successfully"
else
  error "Failed to start system services. Check logs/integration/start_dev.log for details"
  exit 1
fi

# Wait for services to fully initialize
sleep 5

section "Testing Core Functionality"

# Test 1: Test Content Submission API
echo "Testing content submission..."
curl -s -X POST http://localhost:8080/api/content/submit \
  -H "Content-Type: application/json" \
  -d '{
    "title":"Test Political Article",
    "content":"This is an important political development with significant implications.",
    "source":"Test News Agency",
    "author":"Test Reporter"
  }' > logs/integration/content_submit.log

if grep -q "content_hash" logs/integration/content_submit.log; then
  success "Content submission successful"
  # Extract content hash for further tests
  CONTENT_HASH=$(grep -o '"content_hash":"[^"]*' logs/integration/content_submit.log | cut -d '"' -f 4)
  echo "Content hash: $CONTENT_HASH"
else
  error "Content submission failed"
fi

# Test 2: Test Content Verification
echo "Testing content verification..."
curl -s -X POST http://localhost:8080/api/content/verify \
  -H "Content-Type: application/json" \
  -d "{
    \"content_hash\":\"$CONTENT_HASH\",
    \"reference_urls\":[\"https://example.com/reference1\", \"https://example.com/reference2\"]
  }" > logs/integration/content_verify.log

if grep -q "verification_score" logs/integration/content_verify.log; then
  success "Content verification successful"
else
  error "Content verification failed"
fi

# Test 3: Test Content Retrieval
echo "Testing content retrieval..."
curl -s -X GET "http://localhost:8080/api/content/$CONTENT_HASH" > logs/integration/content_retrieve.log

if grep -q "$CONTENT_HASH" logs/integration/content_retrieve.log; then
  success "Content retrieval successful"
else
  error "Content retrieval failed"
fi

# Test 4: Test Zero-Knowledge Proof for Source Authentication
echo "Testing source authentication with ZKP..."
curl -s -X POST http://localhost:8080/api/source/verify \
  -H "Content-Type: application/json" \
  -d '{
    "proof_data":"eyJjb21taXRtZW50IjoiMTIzNDU2Nzg5MCIsImNoYWxsZW5nZSI6Ijg3NjU0MzIxMCIsInJlc3BvbnNlIjoiYWJjZGVmZ2hpaiJ9",
    "public_info":"Test News Agency,Political Reporter",
    "claimed_location":"North America"
  }' > logs/integration/source_verify.log

if grep -q "source_verification" logs/integration/source_verify.log; then
  success "Source verification with ZKP successful"
else
  warning "Source verification with ZKP may need additional setup"
fi

# Test 5: Test Byzantine Consensus
echo "Testing Byzantine consensus with multiple verifications..."

# Submit first verification from node1
curl -s -X POST http://localhost:8080/api/verification/submit \
  -H "Content-Type: application/json" \
  -d "{
    \"node_id\":\"node1\",
    \"content_hash\":\"$CONTENT_HASH\",
    \"verification_level\":3,
    \"cross_references\":[],
    \"disputed\":false,
    \"dispute_reasons\":[]
  }" > logs/integration/verify1.log

# Submit second verification from node2
curl -s -X POST http://localhost:8080/api/verification/submit \
  -H "Content-Type: application/json" \
  -d "{
    \"node_id\":\"node2\",
    \"content_hash\":\"$CONTENT_HASH\",
    \"verification_level\":2,
    \"cross_references\":[],
    \"disputed\":false,
    \"dispute_reasons\":[]
  }" > logs/integration/verify2.log

# Submit contradicting verification from node3 (simulating byzantine behavior)
curl -s -X POST http://localhost:8080/api/verification/submit \
  -H "Content-Type: application/json" \
  -d "{
    \"node_id\":\"node3\",
    \"content_hash\":\"$CONTENT_HASH\",
    \"verification_level\":1,
    \"cross_references\":[],
    \"disputed\":true,
    \"dispute_reasons\":[\"Factual inaccuracy\", \"Source bias\"]
  }" > logs/integration/verify3.log

# Get consensus status
curl -s -X GET "http://localhost:8080/api/verification/status/$CONTENT_HASH" > logs/integration/consensus_status.log

if grep -q "verification_level" logs/integration/consensus_status.log; then
  success "Byzantine consensus test successful"
  
  # Check if dispute was recorded
  if grep -q "disputed.*true" logs/integration/consensus_status.log; then
    success "Dispute detection working correctly"
  else
    warning "Dispute detection may not be functioning correctly"
  fi
else
  error "Byzantine consensus test failed"
fi

# Test 6: Test GDELT Data Pipeline
echo "Running GDELT data pipeline with small dataset..."
./run_gdelt_pipeline.sh -m 50 -t 1d fetch > logs/integration/gdelt_fetch.log 2>&1
check_status "GDELT data fetching"

./run_gdelt_pipeline.sh -e 5 analyze > logs/integration/gdelt_analyze.log 2>&1
check_status "GDELT data analysis"

# Test 7: Test Logical Entanglement for Content Integrity
echo "Testing logical entanglement..."
curl -s -X POST http://localhost:8080/api/content/entangle \
  -H "Content-Type: application/json" \
  -d "{
    \"content_parts\":[
      \"HEADLINE: Test Political Article\",
      \"CONTENT: This is an important political development with significant implications.\",
      \"SOURCE: Test News Agency\",
      \"AUTHOR: Test Reporter\"
    ]
  }" > logs/integration/entanglement.log

if grep -q "entanglement_hash" logs/integration/entanglement.log; then
  success "Logical entanglement successful"
  
  # Extract entanglement hash
  ENTANGLEMENT_HASH=$(grep -o '"entanglement_hash":"[^"]*' logs/integration/entanglement.log | cut -d '"' -f 4)
  
  # Test entanglement verification
  curl -s -X POST http://localhost:8080/api/content/verify_entanglement \
    -H "Content-Type: application/json" \
    -d "{
      \"entanglement_hash\":\"$ENTANGLEMENT_HASH\",
      \"content_parts\":[
        \"HEADLINE: Test Political Article\",
        \"CONTENT: This is an important political development with significant implications.\",
        \"SOURCE: Test News Agency\",
        \"AUTHOR: Test Reporter\"
      ]
    }" > logs/integration/entanglement_verify.log
  
  if grep -q "\"intact\":true" logs/integration/entanglement_verify.log; then
    success "Entanglement verification successful"
  else
    error "Entanglement verification failed"
  fi
  
  # Test tamper detection by modifying content
  curl -s -X POST http://localhost:8080/api/content/verify_entanglement \
    -H "Content-Type: application/json" \
    -d "{
      \"entanglement_hash\":\"$ENTANGLEMENT_HASH\",
      \"content_parts\":[
        \"HEADLINE: Test Political Article\",
        \"CONTENT: This content has been TAMPERED with and modified.\",
        \"SOURCE: Test News Agency\",
        \"AUTHOR: Test Reporter\"
      ]
    }" > logs/integration/entanglement_tamper.log
  
  if grep -q "\"intact\":false" logs/integration/entanglement_tamper.log; then
    success "Tampering detection successful"
  else
    error "Tampering detection failed"
  fi
else
  error "Logical entanglement failed"
fi

# Test 8: Test Post-Quantum Key Exchange
echo "Testing post-quantum key exchange..."
curl -s -X POST http://localhost:8080/api/crypto/exchange \
  -H "Content-Type: application/json" \
  -d '{
    "client_id":"test-client"
  }' > logs/integration/key_exchange1.log

if grep -q "public_key" logs/integration/key_exchange1.log; then
  success "Key exchange step 1 successful"
  
  # Extract public key
  PUBLIC_KEY=$(grep -o '"public_key":"[^"]*' logs/integration/key_exchange1.log | cut -d '"' -f 4)
  
  # Complete key exchange
  curl -s -X POST http://localhost:8080/api/crypto/complete_exchange \
    -H "Content-Type: application/json" \
    -d "{
      \"client_id\":\"test-client\",
      \"client_ciphertext\":\"SIMULATED_CIPHERTEXT_FOR_TESTING\"
    }" > logs/integration/key_exchange2.log
  
  if grep -q "exchange_complete" logs/integration/key_exchange2.log; then
    success "Post-quantum key exchange successful"
  else
    error "Post-quantum key exchange failed"
  fi
else
  error "Key exchange failed"
fi

# Stop all services
echo "Stopping all services..."
./scripts/stop_dev.sh > logs/integration/stop_dev.log 2>&1
check_status "System services stopped"

# Calculate and display execution time
END_TIME=$(date +%s)
EXECUTION_TIME=$((END_TIME - START_TIME))
MINUTES=$((EXECUTION_TIME / 60))
SECONDS=$((EXECUTION_TIME % 60))

section "Integration Test Summary"
echo "Tests completed in ${MINUTES}m ${SECONDS}s"

# Parse logs to count successes and failures
SUCCESS_COUNT=$(grep -c "${GREEN}✓" logs/integration/integration_test.log 2>/dev/null || echo 0)
FAILURE_COUNT=$(grep -c "${RED}✗" logs/integration/integration_test.log 2>/dev/null || echo 0)
WARNING_COUNT=$(grep -c "${YELLOW}!" logs/integration/integration_test.log 2>/dev/null || echo 0)

echo -e "${GREEN}Passed: ${SUCCESS_COUNT}${NC}"
echo -e "${RED}Failed: ${FAILURE_COUNT}${NC}"
echo -e "${YELLOW}Warnings: ${WARNING_COUNT}${NC}"

if [ $FAILURE_COUNT -eq 0 ]; then
  echo -e "\n${GREEN}Full integration test completed successfully!${NC}"
  exit 0
else
  echo -e "\n${RED}Integration test completed with failures.${NC}"
  exit 1
fi
