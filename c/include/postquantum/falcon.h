/**
 * falcon.h
 * 
 * Implementation of the Falcon signature scheme
 * Based on the NIST PQC standardized algorithm for post-quantum secure digital signatures
 * Using Algorand's Falcon implementation
 * 
 * Reference: https://falcon-sign.info/
 */

#ifndef FALCON_H
#define FALCON_H

#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>

/**
 * Falcon security parameters for Falcon-512 (NIST Security Level 1)
 */
#define FALCON_PUBLIC_KEY_BYTES 897
#define FALCON_SECRET_KEY_BYTES 1281
#define FALCON_SIGNATURE_MAX_BYTES 666 // Maximum size; actual size may be smaller

/**
 * Error codes
 */
#define FALCON_ERR_RANDOM     -1  // RNG failed
#define FALCON_ERR_SIZE       -2  // Buffer too small
#define FALCON_ERR_FORMAT     -3  // Invalid format
#define FALCON_ERR_BADSIG     -4  // Invalid signature
#define FALCON_ERR_BADARG     -5  // Invalid argument
#define FALCON_ERR_INTERNAL   -6  // Internal error

/**
 * Falcon keypair structure
 */
typedef struct {
    uint8_t public_key[FALCON_PUBLIC_KEY_BYTES];
    uint8_t secret_key[FALCON_SECRET_KEY_BYTES];
} falcon_keypair_t;

/**
 * Initialize the Falcon signature scheme
 * Must be called before using any other functions
 * 
 * @return 0 on success, error code otherwise
 */
int falcon_init(void);

/**
 * Generate a new Falcon keypair
 * 
 * @param keypair Pointer to a falcon_keypair_t structure to store the generated keys
 * @return 0 on success, error code otherwise
 */
int falcon_keygen(falcon_keypair_t* keypair);

/**
 * Sign a message with Falcon
 * 
 * @param signature Buffer to store the signature
 * @param signature_len Pointer to store the actual length of the signature
 * @param message The message to sign
 * @param message_len Length of the message in bytes
 * @param secret_key The signer's secret key
 * @return 0 on success, error code otherwise
 */
int falcon_sign(
    uint8_t* signature,
    size_t* signature_len,
    const uint8_t* message,
    size_t message_len,
    const uint8_t* secret_key
);

/**
 * Verify a Falcon signature
 * 
 * @param signature The signature to verify
 * @param signature_len Length of the signature in bytes
 * @param message The message that was signed
 * @param message_len Length of the message in bytes
 * @param public_key The signer's public key
 * @return 1 if signature is valid, 0 if invalid, negative value on error
 */
int falcon_verify(
    const uint8_t* signature,
    size_t signature_len,
    const uint8_t* message,
    size_t message_len,
    const uint8_t* public_key
);

/**
 * Clean up the Falcon signature scheme
 * Must be called when Falcon is no longer needed
 */
void falcon_cleanup(void);

#endif /* FALCON_H */
