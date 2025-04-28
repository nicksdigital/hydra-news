#!/bin/bash
# Hydra News Complete Test Suite Runner
# This script runs all tests for the Hydra News system and generates a comprehensive report

# Set colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Set test report file
TEST_REPORT="test_results/test_report.md"
HTML_REPORT="test_results/test_report.html"

# Function to print section headers
section() {
  echo -e "\n${BLUE}==== $1 ====${NC}"
  echo -e "## $1\n" >> $TEST_REPORT
}

# Function for success messages
success() {
  echo -e "${GREEN}✓ $1${NC}"
  echo -e "- ✅ $1" >> $TEST_REPORT
}

# Function for error messages
error() {
  echo -e "${RED}✗ $1${NC}"
  echo -e "- ❌ $1" >> $TEST_REPORT
}

# Function for warning messages
warning() {
  echo -e "${YELLOW}! $1${NC}"
  echo -e "- ⚠️ $1" >> $TEST_REPORT
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

# Create results directory
mkdir -p test_results
mkdir -p logs/tests

# Record start time
START_TIME=$(date +%s)

# Start test report
echo "# Hydra News Test Report" > $TEST_REPORT
echo "Generated on $(date)" >> $TEST_REPORT
echo "" >> $TEST_REPORT

# Run comprehensive test script
section "Running comprehensive system tests"
chmod +x hydra_news_test.sh
./hydra_news_test.sh > logs/tests/comprehensive_tests.log 2>&1
check_status "Comprehensive system tests"

# Run individual component tests

# 1. C Cryptographic Components
section "Testing C Cryptographic Components"
echo "Building and testing C components..."
cd c
make clean > /dev/null 2>&1
make > ../logs/tests/c_build.log 2>&1
check_status "Build C components"

# Check if tests directory exists
if [ -d "tests" ]; then
  mkdir -p build
  gcc -I./include -L./lib ./tests/test_crypto_adapter.c -lqzkp -lle -lkyber -lfalcon -lcryptoadapter -o build/test_crypto_adapter > ../logs/tests/crypto_adapter_build.log 2>&1
  
  if [ -f "build/test_crypto_adapter" ]; then
    LD_LIBRARY_PATH=./lib ./build/test_crypto_adapter > ../logs/tests/crypto_adapter_test.log 2>&1
    check_status "Post-quantum cryptography tests"
  else
    error "Failed to build crypto adapter tests"
  fi
else
  warning "No C tests found, skipping cryptographic component tests"
fi
cd ..

# 2. Go Consensus Network Tests
section "Testing Go Consensus Network"
cd go
go mod init hydranews 2>/dev/null || true
go get -u github.com/gorilla/mux > /dev/null 2>&1
go get -u github.com/rs/cors > /dev/null 2>&1

# Run Go tests
if [ -d "consensus" ]; then
  go test -v ./consensus > ../logs/tests/go_consensus_tests.log 2>&1
  check_status "Byzantine fault-tolerant consensus tests"
else
  warning "No consensus tests found, skipping Go consensus tests"
fi
cd ..

# 3. Python Content Processor Tests
section "Testing Python Content Processor"
cd python
pip install -r requirements.txt > ../logs/tests/pip_install.log 2>&1
check_status "Install Python dependencies"

# Run Python tests
if [ -d "tests" ]; then
  python -m pytest tests/ -v > ../logs/tests/python_tests.log 2>&1
  check_status "Content processor tests"
else
  warning "No Python tests found, skipping content processor tests"
fi
cd ..

# 4. GDELT News Prediction Model Tests
section "Testing GDELT News Prediction Model"
chmod +x test_prediction_model.py
./test_prediction_model.py --dataset-dir analysis_gdelt_enhanced --output-dir test_results/prediction > logs/tests/prediction_model_tests.log 2>&1
check_status "News prediction model tests"

# 5. Integration Tests
section "Testing Full System Integration"
./scripts/start_dev.sh > logs/tests/system_start.log 2>&1

if grep -q "Development environment started" logs/tests/system_start.log; then
  success "System successfully started"
  
  # Give some time for the system to initialize
  sleep 5
  
  # Test API endpoints
  curl -s http://localhost:8080/api/status > logs/tests/api_status.log 2>&1
  STATUS_CODE=$?
  
  if [ $STATUS_CODE -eq 0 ]; then
    success "API is responding"
  else
    error "API is not responding"
  fi
  
  # Test GDELT pipeline with small dataset
  ./run_gdelt_pipeline.sh -m 100 -t 1d fetch > logs/tests/gdelt_fetch_test.log 2>&1
  check_status "GDELT data fetching"
  
  ./run_gdelt_pipeline.sh -e 5 analyze > logs/tests/gdelt_analyze_test.log 2>&1
  check_status "GDELT data analysis"
  
  # Stop the system
  ./scripts/stop_dev.sh > logs/tests/system_stop.log 2>&1
  check_status "System successfully stopped"
else
  error "System failed to start"
fi

# 6. Security Tests
section "Running Security Tests"

# Test Byzantine fault tolerance
echo "Testing Byzantine fault tolerance with simulated malicious nodes..."
cd go
if [ -d "consensus" ]; then
  go test -v ./consensus -run=TestByzantineFaultTolerance > ../logs/tests/bft_security_tests.log 2>&1
  check_status "Byzantine fault tolerance security test"
else
  warning "Consensus module not found, skipping Byzantine fault tolerance test"
fi
cd ..

# Test post-quantum cryptography
echo "Testing post-quantum cryptography against simulated attacks..."
cd c
if [ -f "build/test_crypto_adapter" ]; then
  LD_LIBRARY_PATH=./lib ./build/test_crypto_adapter --security-test > ../logs/tests/pq_crypto_security_tests.log 2>&1
  check_status "Post-quantum cryptography security test"
else
  warning "Crypto adapter test not found, skipping post-quantum security test"
fi
cd ..

# Test source protection
echo "Testing source protection mechanisms..."
cd python
python -m tests.test_source_protection > ../logs/tests/source_protection_tests.log 2>&1
check_status "Source protection security test"
cd ..

# 7. Performance Tests
section "Running Performance Tests"

# Test cryptographic operations performance
echo "Testing cryptographic operations performance..."
cd c
if [ -f "build/test_crypto_adapter" ]; then
  LD_LIBRARY_PATH=./lib ./build/test_crypto_adapter --performance-test > ../logs/tests/crypto_performance_tests.log 2>&1
  check_status "Cryptographic operations performance test"
else
  warning "Crypto adapter test not found, skipping crypto performance test"
fi
cd ..

# Test consensus network scalability
echo "Testing consensus network scalability..."
cd go
if [ -d "consensus" ]; then
  go test -v ./consensus -run=TestLargeNetworkScalability > ../logs/tests/consensus_scalability_tests.log 2>&1
  check_status "Consensus network scalability test"
else
  warning "Consensus module not found, skipping consensus scalability test"
fi
cd ..

# Test GDELT prediction model performance
echo "Testing GDELT prediction model performance..."
./test_prediction_model.py --dataset-dir analysis_gdelt_enhanced --output-dir test_results/prediction --test-all-entities > logs/tests/prediction_performance_tests.log 2>&1
check_status "Prediction model performance test"

# Generate summary statistics and charts
section "Generating Test Summary"

# Calculate and display execution time
END_TIME=$(date +%s)
EXECUTION_TIME=$((END_TIME - START_TIME))
MINUTES=$((EXECUTION_TIME / 60))
SECONDS=$((EXECUTION_TIME % 60))

echo -e "\nTests completed in ${MINUTES}m ${SECONDS}s"
echo -e "\n## Test Summary\n" >> $TEST_REPORT
echo -e "Tests completed in ${MINUTES}m ${SECONDS}s\n" >> $TEST_REPORT

# Count success and failures
SUCCESS_COUNT=$(grep -c "- ✅" $TEST_REPORT)
FAILURE_COUNT=$(grep -c "- ❌" $TEST_REPORT)
WARNING_COUNT=$(grep -c "- ⚠️" $TEST_REPORT)

echo -e "${GREEN}Passed: ${SUCCESS_COUNT}${NC}"
echo -e "${RED}Failed: ${FAILURE_COUNT}${NC}"
echo -e "${YELLOW}Warnings: ${WARNING_COUNT}${NC}"

echo -e "- **Passed**: ${SUCCESS_COUNT}" >> $TEST_REPORT
echo -e "- **Failed**: ${FAILURE_COUNT}" >> $TEST_REPORT
echo -e "- **Warnings**: ${WARNING_COUNT}" >> $TEST_REPORT

# Calculate pass rate
TOTAL_TESTS=$((SUCCESS_COUNT + FAILURE_COUNT))
if [ $TOTAL_TESTS -gt 0 ]; then
  PASS_RATE=$((SUCCESS_COUNT * 100 / TOTAL_TESTS))
  echo -e "- **Pass Rate**: ${PASS_RATE}%" >> $TEST_REPORT
  
  if [ $PASS_RATE -ge 90 ]; then
    echo -e "\n### 🟢 System Health: GOOD" >> $TEST_REPORT
  elif [ $PASS_RATE -ge 75 ]; then
    echo -e "\n### 🟡 System Health: ACCEPTABLE" >> $TEST_REPORT
  else
    echo -e "\n### 🔴 System Health: NEEDS ATTENTION" >> $TEST_REPORT
  fi
fi

# Generate HTML report
echo "Converting test report to HTML..."
echo '<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Hydra News Test Report</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 0; padding: 20px; color: #333; }
    h1 { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }
    h2 { color: #2980b9; margin-top: 30px; }
    h3 { color: #3498db; }
    .success { color: #27ae60; }
    .error { color: #e74c3c; }
    .warning { color: #f39c12; }
    .summary { background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 30px; }
    ul { list-style-type: none; padding-left: 20px; }
    li { margin-bottom: 5px; }
  </style>
</head>
<body>' > $HTML_REPORT

# Convert markdown to simple HTML
cat $TEST_REPORT | sed 's/# \(.*\)/<h1>\1<\/h1>/g' | \
                   sed 's/## \(.*\)/<h2>\1<\/h2>/g' | \
                   sed 's/### \(.*\)/<h3>\1<\/h3>/g' | \
                   sed 's/- ✅ \(.*\)/<li>✅ <span class="success">\1<\/span><\/li>/g' | \
                   sed 's/- ❌ \(.*\)/<li>❌ <span class="error">\1<\/span><\/li>/g' | \
                   sed 's/- ⚠️ \(.*\)/<li>⚠️ <span class="warning">\1<\/span><\/li>/g' | \
                   sed 's/- \*\*\(.*\)\*\*: \(.*\)/<li><strong>\1<\/strong>: \2<\/li>/g' | \
                   sed '/^$/d' | \
                   sed 's/^[^<]/&nbsp;&nbsp;\0/g' | \
                   sed 's/^[^<]/<p>\0<\/p>/g' >> $HTML_REPORT

echo '</body></html>' >> $HTML_REPORT

echo -e "\nTest report generated at $TEST_REPORT"
echo -e "HTML report generated at $HTML_REPORT"

if [ $FAILURE_COUNT -eq 0 ]; then
  echo -e "\n${GREEN}All critical tests passed!${NC}"
  exit 0
else
  echo -e "\n${RED}Some tests failed. Review $TEST_REPORT for details.${NC}"
  exit 1
fi
