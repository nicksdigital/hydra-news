CC = gcc
CFLAGS = -Wall -Wextra -I../c/src
LDFLAGS = -lm -lcrypto
SRCDIR = ../c/src
TESTDIR = .

# Source files
SOURCES = $(SRCDIR)/quantum_zkp.c
HEADERS = $(SRCDIR)/quantum_zkp.h $(SRCDIR)/logical_entanglement.h

# Test files
TEST_SRC = $(TESTDIR)/test_anonymity.c
TEST_BIN = test_anonymity

.PHONY: all clean run

all: $(TEST_BIN)

$(TEST_BIN): $(TEST_SRC) $(SOURCES) $(HEADERS)
	$(CC) $(CFLAGS) -o $@ $(TEST_SRC) $(SOURCES) $(LDFLAGS)

run: $(TEST_BIN)
	./$(TEST_BIN)

clean:
	rm -f $(TEST_BIN)
