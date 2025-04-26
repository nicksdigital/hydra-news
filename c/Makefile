# Makefile for Hydra News C libraries

# Compiler settings
CC := gcc
CFLAGS := -Wall -Wextra -fPIC -O2 -Isrc
LDFLAGS := -shared -lcrypto -lssl

# Directories
SRC_DIR := src
BUILD_DIR := build
LIB_DIR := lib
INCLUDE_DIR := include

# Source files
QZKP_SRC := $(SRC_DIR)/quantum_zkp.c
LE_SRC := $(SRC_DIR)/logical_entanglement.c
KYBER_SRC := $(SRC_DIR)/postquantum/kyber.c
FALCON_SRC := $(SRC_DIR)/postquantum/falcon.c
CRYPTO_ADAPTER_SRC := $(SRC_DIR)/postquantum/crypto_adapter.c
HYDRA_SRC := $(SRC_DIR)/hydra_cgo.c

# Output libraries
QZKP_LIB := $(LIB_DIR)/libqzkp.so
LE_LIB := $(LIB_DIR)/lible.so
KYBER_LIB := $(LIB_DIR)/libkyber.so
FALCON_LIB := $(LIB_DIR)/libfalcon.so
CRYPTO_ADAPTER_LIB := $(LIB_DIR)/libcryptoadapter.so
HYDRA_LIB := $(LIB_DIR)/libhydra.so

# All libraries in one (for CGO)
COMBINED_LIB := $(LIB_DIR)/libhydracrypto.so

# Object files
QZKP_OBJ := $(BUILD_DIR)/quantum_zkp.o
LE_OBJ := $(BUILD_DIR)/logical_entanglement.o
KYBER_OBJ := $(BUILD_DIR)/kyber.o
FALCON_OBJ := $(BUILD_DIR)/falcon.o
CRYPTO_ADAPTER_OBJ := $(BUILD_DIR)/crypto_adapter.o
HYDRA_OBJ := $(BUILD_DIR)/hydra_cgo.o

# Headers to install
HEADERS := $(QZKP_HEADER) $(LE_HEADER) $(KYBER_HEADER) $(FALCON_HEADER) $(CRYPTO_ADAPTER_HEADER) $(HYDRA_HEADER)

# Default target
all: libs headers

# Create directories
dirs:
	mkdir -p $(BUILD_DIR) $(LIB_DIR) $(INCLUDE_DIR)

# Build individual libraries
libs: dirs $(QZKP_LIB) $(LE_LIB) $(KYBER_LIB) $(FALCON_LIB) $(CRYPTO_ADAPTER_LIB) $(HYDRA_LIB) $(COMBINED_LIB)

# Install headers
headers: dirs
	cp $(SRC_DIR)/quantum_zkp.h $(INCLUDE_DIR)/
	cp $(SRC_DIR)/logical_entanglement.h $(INCLUDE_DIR)/
	cp $(SRC_DIR)/postquantum/kyber.h $(INCLUDE_DIR)/
	cp $(SRC_DIR)/postquantum/falcon.h $(INCLUDE_DIR)/
	cp $(SRC_DIR)/postquantum/crypto_adapter.h $(INCLUDE_DIR)/
	cp $(SRC_DIR)/hydra_cgo.h $(INCLUDE_DIR)/

# QZKP library
$(QZKP_LIB): $(QZKP_OBJ)
	$(CC) $(LDFLAGS) -o $@ $<

$(QZKP_OBJ): $(QZKP_SRC)
	$(CC) $(CFLAGS) -c $< -o $@

# Logical Entanglement library
$(LE_LIB): $(LE_OBJ)
	$(CC) $(LDFLAGS) -o $@ $<

$(LE_OBJ): $(LE_SRC)
	$(CC) $(CFLAGS) -c $< -o $@

# Kyber library
$(KYBER_LIB): $(KYBER_OBJ)
	$(CC) $(LDFLAGS) -o $@ $<

$(KYBER_OBJ): $(KYBER_SRC)
	$(CC) $(CFLAGS) -c $< -o $@

# Falcon library
$(FALCON_LIB): $(FALCON_OBJ)
	$(CC) $(LDFLAGS) -o $@ $<

$(FALCON_OBJ): $(FALCON_SRC)
	$(CC) $(CFLAGS) -c $< -o $@

# Crypto Adapter library
$(CRYPTO_ADAPTER_LIB): $(CRYPTO_ADAPTER_OBJ)
	$(CC) $(LDFLAGS) -o $@ $< -L$(LIB_DIR) -lqzkp -lkyber -lfalcon

$(CRYPTO_ADAPTER_OBJ): $(CRYPTO_ADAPTER_SRC)
	$(CC) $(CFLAGS) -c $< -o $@

# Hydra CGO library
$(HYDRA_LIB): $(HYDRA_OBJ)
	$(CC) $(LDFLAGS) -o $@ $< -L$(LIB_DIR) -lqzkp -lle -lkyber -lfalcon -lcryptoadapter

$(HYDRA_OBJ): $(HYDRA_SRC)
	$(CC) $(CFLAGS) -c $< -o $@

# Combined library
$(COMBINED_LIB): $(QZKP_OBJ) $(LE_OBJ) $(KYBER_OBJ) $(FALCON_OBJ) $(CRYPTO_ADAPTER_OBJ) $(HYDRA_OBJ)
	$(CC) $(LDFLAGS) -o $@ $^

# Clean target
clean:
	rm -f $(BUILD_DIR)/*.o $(LIB_DIR)/*.so

# Rebuild everything
rebuild: clean all

.PHONY: all dirs libs headers clean rebuild
