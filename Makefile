# Hydra News Makefile

# Directory paths
ROOT_DIR := $(shell pwd)
C_DIR := $(ROOT_DIR)/c
GO_DIR := $(ROOT_DIR)/go
PYTHON_DIR := $(ROOT_DIR)/python
TS_DIR := $(ROOT_DIR)/typescript

# Build output directories
OUTPUT_DIR := $(ROOT_DIR)/build
LIB_DIR := $(C_DIR)/lib
BIN_DIR := $(OUTPUT_DIR)/bin

# C compiler settings
CC := gcc
CFLAGS := -Wall -Wextra -fPIC -O2 -I$(C_DIR)/src
LDFLAGS := -shared -lcrypto -lssl

# Go compiler settings
GOFLAGS := -ldflags="-s -w"

# Python settings
PYTHON := python3
VENV_DIR := $(ROOT_DIR)/venv

# Files to build
C_SRC_FILES := $(C_DIR)/src/quantum_zkp.c \
               $(C_DIR)/src/postquantum/kyber.c \
               $(C_DIR)/src/postquantum/falcon.c \
               $(C_DIR)/src/postquantum/crypto_adapter.c

# Output libraries
QZKP_LIB := $(LIB_DIR)/libqzkp.so
KYBER_LIB := $(LIB_DIR)/libkyber.so
FALCON_LIB := $(LIB_DIR)/libfalcon.so

# Main binaries
GO_BIN := $(BIN_DIR)/hydra-news-api

# Create required directories
$(shell mkdir -p $(LIB_DIR) $(BIN_DIR))

# Default target
all: c-libs go-build python-setup

# Build C libraries
c-libs: $(QZKP_LIB) $(KYBER_LIB) $(FALCON_LIB)

$(QZKP_LIB): $(C_DIR)/src/quantum_zkp.c $(C_DIR)/src/quantum_zkp.h
	@echo "Building QZKP library..."
	$(CC) $(CFLAGS) -o $@ $< $(LDFLAGS)

$(KYBER_LIB): $(C_DIR)/src/postquantum/kyber.c $(C_DIR)/src/postquantum/kyber.h
	@echo "Building Kyber library..."
	$(CC) $(CFLAGS) -o $@ $< $(LDFLAGS)

$(FALCON_LIB): $(C_DIR)/src/postquantum/falcon.c $(C_DIR)/src/postquantum/falcon.h
	@echo "Building Falcon library..."
	$(CC) $(CFLAGS) -o $@ $< $(LDFLAGS)

# Build Go application
go-build: c-libs
	@echo "Building Go application..."
	cd $(GO_DIR) && CGO_ENABLED=1 LD_LIBRARY_PATH=$(LIB_DIR) \
		go build $(GOFLAGS) -o $(GO_BIN) .

# Set up Python environment
python-setup:
	@echo "Setting up Python environment..."
	test -d $(VENV_DIR) || $(PYTHON) -m venv $(VENV_DIR)
	. $(VENV_DIR)/bin/activate && \
		pip install --upgrade pip && \
		pip install -r $(PYTHON_DIR)/requirements.txt

# Run tests
test: c-libs
	@echo "Running tests..."
	cd $(GO_DIR) && CGO_ENABLED=1 LD_LIBRARY_PATH=$(LIB_DIR) \
		go test ./...

# Run the application
run: go-build
	@echo "Running Hydra News API..."
	LD_LIBRARY_PATH=$(LIB_DIR) $(GO_BIN)

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	rm -rf $(LIB_DIR)/* $(BIN_DIR)/*
	cd $(GO_DIR) && go clean

# Install dependencies
deps:
	@echo "Installing dependencies..."
	apt-get update && apt-get install -y \
		build-essential \
		libssl-dev \
		pkg-config \
		golang \
		python3 \
		python3-venv \
		python3-pip \
		nodejs \
		npm

# Help target
help:
	@echo "Hydra News Build System"
	@echo "----------------------"
	@echo "Available targets:"
	@echo "  all         : Build everything (default)"
	@echo "  c-libs      : Build C libraries only"
	@echo "  go-build    : Build Go application"
	@echo "  python-setup: Set up Python environment"
	@echo "  test        : Run tests"
	@echo "  run         : Build and run the application"
	@echo "  clean       : Clean build artifacts"
	@echo "  deps        : Install system dependencies"
	@echo "  help        : Show this help message"

.PHONY: all c-libs go-build python-setup test run clean deps help
