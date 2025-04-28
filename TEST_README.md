# Hydra News Testing Framework

## Introduction

This document provides detailed instructions for using the Hydra News testing framework. The testing system validates all components of the Hydra News platform, including post-quantum cryptography, Byzantine fault-tolerant consensus, source protection, content integrity verification, and predictive analytics.

The testing framework is critical for ensuring the reliability and security of the Hydra News system, which is designed to protect sources and ensure the integrity of news content.

## Prerequisites

Before running the tests, ensure the following dependencies are installed:

- Go 1.21+
- Python 3.10+
- GCC/Clang compiler
- OpenSSL development libraries
- curl

On Ubuntu, you can install these dependencies with:

```bash
sudo apt update
sudo apt install golang python3 python3-pip python3-venv gcc libssl-dev curl
```

## Quick Start

To run the complete test suite with default settings:

```bash
cd /home/ubuntu/hydra-news
chmod +x run_all_tests.sh
./run_all_tests.sh
```

This will run all components of the test suite and generate a detailed report in both Markdown and HTML formats in the `test_results` directory.

## Test Components

### 1. Comprehensive System Test (`hydra_news_test.sh`)

This script runs a complete system test, checking all components of the Hydra News platform:

```bash
./hydra_news_test.sh
```

It performs the following tests:
- Dependency validation
- C cryptographic primitives tests
- Go consensus network tests
- Python content processor tests
- GDELT pipeline tests with a small dataset
- Full system integration testing

### 2. C Cryptographic Tests (`c/tests/test_crypto_adapter.c`)

These tests validate the post-quantum cryptographic components:

```bash
cd c
make
LD_LIBRARY_PATH=./lib ./build/test_crypto_adapter
```

Test options:
- `--security-test`: Run only security-focused tests
- `--performance-test`: Run only performance benchmarks

### 3. Go Consensus Network Tests (`go/consensus/consensus_test.go`)

These tests validate the Byzantine fault-tolerant consensus network:

```bash
cd go
go test -v ./consensus
```

Individual test cases:
- `TestConsensusBasic`: Basic consensus functionality
- `TestByzantineFaultTolerance`: Resistance to malicious nodes
- `TestConcurrentProposals`: Handling multiple concurrent proposals
- `TestNetworkPartition`: Resilience to network partitions
- `TestLargeNetworkScalability`: Performance with large networks
- `TestSourceAuthenticity`: Source verification mechanisms
- `TestGeolocationVerification`: Location verification with privacy

### 4. GDELT Prediction Model Tests (`test_prediction_model.py`)

These tests validate the news prediction model:

```bash
./test_prediction_model.py --dataset-dir analysis_gdelt_enhanced --output-dir test_results/prediction
```

Options:
- `--dataset-dir`: Directory containing GDELT dataset
- `--output-dir`: Directory to save test results
- `--entity`: Specific entity to test (default: test all entities)
- `--days-to-predict`: Number of days to predict (default: 7)
- `--training-days`: Number of days to use for training (default: 30)
- `--models`: Comma-separated list of models to test (default: arima,prophet)
- `--test-all-entities`: Test all entities in the dataset

## Running Security Tests

To focus specifically on security testing:

```bash
# Run security-focused tests on all components
./run_all_tests.sh --security-only

# Test Byzantine fault tolerance specifically
cd go
go test -v ./consensus -run=TestByzantineFaultTolerance

# Test post-quantum cryptography against attacks
cd c
LD_LIBRARY_PATH=./lib ./build/test_crypto_adapter --security-test
```

## Running Performance Tests

To focus on performance testing:

```bash
# Run performance-focused tests on all components
./run_all_tests.sh --performance-only

# Test cryptographic operation performance
cd c
LD_LIBRARY_PATH=./lib ./build/test_crypto_adapter --performance-test

# Test consensus network scalability
cd go
go test -v ./consensus -run=TestLargeNetworkScalability
```

## Test Reporting

All tests generate detailed logs and reports:

### Log Files

- System tests: `logs/tests/comprehensive_tests.log`
- C component tests: `logs/tests/crypto_adapter_test.log`
- Go consensus tests: `logs/tests/go_consensus_tests.log`
- Python tests: `logs/tests/python_tests.log`
- Prediction model tests: `logs/tests/prediction_model_tests.log`

### Test Reports

- Markdown report: `test_results/test_report.md`
- HTML report: `test_results/test_report.html`

## Troubleshooting

### Common Issues

1. **Library Not Found Errors**:
   ```
   error while loading shared libraries: libqzkp.so: cannot open shared object file
   ```
   Solution: Set the library path correctly:
   ```bash
   export LD_LIBRARY_PATH=/home/ubuntu/hydra-news/c/lib:$LD_LIBRARY_PATH
   ```

2. **Go Module Issues**:
   ```
   cannot find module providing package hydranews/consensus
   ```
   Solution: Initialize Go modules properly:
   ```bash
   cd go
   go mod init hydranews
   go mod tidy
   ```

3. **Python Environment Issues**:
   ```
   ModuleNotFoundError: No module named 'xyz'
   ```
   Solution: Ensure Python dependencies are installed:
   ```bash
   pip install -r requirements.txt
   ```

4. **Network Port Conflicts**:
   ```
   listen tcp :8080: bind: address already in use
   ```
   Solution: Stop any running instances or change the port:
   ```bash
   ./scripts/stop_dev.sh
   # Or modify the port in the config
   ```

## Advanced Testing Scenarios

### 1. Testing with Different Network Configurations

To test with more Byzantine nodes:

```bash
cd go
BFT_TEST_NODES=11 BFT_BYZANTINE_NODES=3 go test -v ./consensus -run=TestByzantineFaultTolerance
```

### 2. Testing with Larger GDELT Datasets

For more comprehensive prediction testing:

```bash
./test_prediction_model.py --dataset-dir analysis_gdelt_large --days-to-predict 30 --training-days 90
```

### 3. Testing Source Protection with Various Identity Types

To test different types of source identity verification:

```bash
cd python
python -m tests.test_source_protection --identity-types=journalist,whistleblower,anonymous
```

### 4. Testing Content Verification with Modified Content

To test content verification with specific tampering patterns:

```bash
cd python
python -m tests.test_content_integrity --tamper-pattern=text,metadata,source
```

## Continuous Integration

The test framework is designed to work with CI/CD systems. A basic CI configuration might look like:

```yaml
steps:
  - name: Install dependencies
    run: |
      sudo apt update
      sudo apt install -y golang python3 python3-pip python3-venv gcc libssl-dev curl

  - name: Run tests
    run: |
      cd /path/to/hydra-news
      ./run_all_tests.sh

  - name: Archive test results
    uses: actions/upload-artifact@v2
    with:
      name: test-results
      path: |
        test_results/
        logs/tests/
```

## Security Considerations

When running tests, be aware of the following security considerations:

1. **Default Keys**: The test framework uses default keys for testing. Never use these keys in production.
2. **Network Isolation**: Run tests in an isolated network environment to prevent unintended interactions.
3. **Resource Consumption**: Some tests (especially Byzantine and large network tests) can consume significant resources.
4. **Data Privacy**: The tests use synthetic or public GDELT data. When testing with real data, ensure proper data protection measures.

## Contributing New Tests

When adding new tests to the framework:

1. Follow the existing test patterns for consistency
2. Add appropriate logging and error handling
3. Ensure tests are deterministic and can run in any environment
4. Add timeout controls to prevent indefinite hangs
5. Document the new tests in the relevant README files

## License

The Hydra News testing framework is released under the same license as the main Hydra News system.
