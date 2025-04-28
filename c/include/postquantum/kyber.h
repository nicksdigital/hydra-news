/**
 * kyber.h
 * 
 * Implementation of CRYSTALS-Kyber key encapsulation mechanism (KEM)
 * Based on the NIST PQC standardized algorithm for post-quantum secure key exchange
 * 
 * Reference: https://pq-crystals.org/kyber/
 */

#ifndef KYBER_H
#define KYBER_H

#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>

/**
 * Kyber security parameters
 * 
 * KYBER_K determines the security level:
 * - KYBER_K = 2: Kyber-512 (NIST Level 1, comparable to AES-128)
 * - KYBER_K = 3: Kyber-768 (NIST Level 3, comparable to AES-192)
 * - KYBER_K = 4: Kyber-1024 (NIST Level 5, comparable to AES-256)
 */
#define KYBER_K 3  // We use Kyber-768 by default for a good balance of security and performance

/* Define key and ciphertext sizes for Kyber-768 */
#define KYBER_PUBLIC_KEY_BYTES 1184
#define KYBER_SECRET_KEY_BYTES 2400
#define KYBER_CIPHERTEXT_BYTES 1088
#define KYBER_SHARED_SECRET_BYTES 32

/**
 * Kyber keypair structure
 */
typedef struct {
    uint8_t public_key[KYBER_PUBLIC_KEY_BYTES];
    uint8_t secret_key[KYBER_SECRET_KEY_BYTES];
} kyber_keypair_t;

/**
 * Initialize the Kyber cryptosystem
 * Must be called before using any other functions
 * 
 * @return 0 on success, error code otherwise
 */
int kyber_init(void);

/**
 * Generate a new Kyber keypair
 * 
 * @param keypair Pointer to a kyber_keypair_t structure to store the generated keys
 * @return 0 on success, error code otherwise
 */
int kyber_keygen(kyber_keypair_t* keypair);

/**
 * Encapsulate a shared secret using a public key
 * 
 * @param ciphertext Buffer to store the encapsulated ciphertext (must be KYBER_CIPHERTEXT_BYTES long)
 * @param shared_secret Buffer to store the shared secret (must be KYBER_SHARED_SECRET_BYTES long)
 * @param public_key The recipient's public key
 * @return 0 on success, error code otherwise
 */
int kyber_encapsulate(
    uint8_t* ciphertext,
    uint8_t* shared_secret,
    const uint8_t* public_key
);

/**
 * Decapsulate a shared secret using a ciphertext and secret key
 * 
 * @param shared_secret Buffer to store the shared secret (must be KYBER_SHARED_SECRET_BYTES long)
 * @param ciphertext The encapsulated ciphertext
 * @param secret_key The recipient's secret key
 * @return 0 on success, error code otherwise
 */
int kyber_decapsulate(
    uint8_t* shared_secret,
    const uint8_t* ciphertext,
    const uint8_t* secret_key
);

/**
 * Clean up the Kyber cryptosystem
 * Must be called when Kyber is no longer needed
 */
void kyber_cleanup(void);

#endif /* KYBER_H */
