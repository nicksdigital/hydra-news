CC = gcc
CFLAGS = -Wall -Wextra -I../c/src -I../c/src/postquantum/falcon_ref -I../c/src/postquantum/kyber_ref
LDFLAGS = -lm -lcrypto

# Source directories
SRCDIR = ../c/src
PQDIR = ../c/src/postquantum
KYBERDIR = ../c/src/postquantum/kyber_ref
FALCONDIR = ../c/src/postquantum/falcon_ref
TESTDIR = .

# Test executables
CRYPTO_TEST = c_crypto_tests
PQ_CRYPTO_TEST = pq_crypto_tests

# Falcon source files
FALCON_SRCS = $(FALCONDIR)/falcon.c $(FALCONDIR)/common.c $(FALCONDIR)/codec.c \
              $(FALCONDIR)/fpr.c $(FALCONDIR)/rng.c $(FALCONDIR)/shake.c \
              $(FALCONDIR)/vrfy.c $(FALCONDIR)/keygen.c $(FALCONDIR)/sign.c

# Kyber source files
KYBER_SRCS = $(KYBERDIR)/kem.c $(KYBERDIR)/indcpa.c $(KYBERDIR)/polyvec.c \
             $(KYBERDIR)/poly.c $(KYBERDIR)/ntt.c $(KYBERDIR)/cbd.c \
             $(KYBERDIR)/reduce.c $(KYBERDIR)/verify.c $(KYBERDIR)/fips202.c

.PHONY: all clean run

all: $(CRYPTO_TEST) $(PQ_CRYPTO_TEST)

$(CRYPTO_TEST): $(TESTDIR)/c_crypto_tests.c $(SRCDIR)/quantum_zkp.c
	$(CC) $(CFLAGS) -o $@ $< $(SRCDIR)/quantum_zkp.c $(LDFLAGS)

$(PQ_CRYPTO_TEST): $(TESTDIR)/pq_crypto_tests.c $(PQDIR)/kyber.c $(PQDIR)/falcon.c $(PQDIR)/crypto_adapter.c $(SRCDIR)/quantum_zkp.c $(FALCON_SRCS) $(KYBER_SRCS)
	$(CC) $(CFLAGS) -o $@ $< $(PQDIR)/kyber.c $(PQDIR)/falcon.c $(PQDIR)/crypto_adapter.c $(SRCDIR)/quantum_zkp.c $(FALCON_SRCS) $(KYBER_SRCS) $(LDFLAGS)

run: $(CRYPTO_TEST) $(PQ_CRYPTO_TEST)
	./$(CRYPTO_TEST)
	./$(PQ_CRYPTO_TEST)

run-crypto: $(CRYPTO_TEST)
	./$(CRYPTO_TEST)

run-pq: $(PQ_CRYPTO_TEST)
	./$(PQ_CRYPTO_TEST)

clean:
	rm -f $(CRYPTO_TEST) $(PQ_CRYPTO_TEST)
