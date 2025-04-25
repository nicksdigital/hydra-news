CC = gcc
CFLAGS = -Wall -Wextra -I../c/src
LDFLAGS = -lm -lcrypto

# Source files
SRCDIR = ../c/src
TESTDIR = .

# Test executables
CRYPTO_TEST = c_crypto_tests

.PHONY: all clean run

all: $(CRYPTO_TEST)

$(CRYPTO_TEST): $(TESTDIR)/c_crypto_tests.c $(SRCDIR)/quantum_zkp.c
	$(CC) $(CFLAGS) -o $@ $< $(SRCDIR)/quantum_zkp.c $(LDFLAGS)

run: $(CRYPTO_TEST)
	./$(CRYPTO_TEST)

clean:
	rm -f $(CRYPTO_TEST)
