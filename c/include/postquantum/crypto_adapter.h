/**
 * crypto_adapter.h
 * 
 * Integration layer for combining post-quantum cryptography with the existing
 * Quantum-ZKP system. This provides a unified interface for cryptographic operations.
 */

#ifndef CRYPTO_ADAPTER_H
#define CRYPTO_ADAPTER_H

#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include "../quantum_zkp.h"
#include "kyber.h"
#include "falcon.h"

/**
 * Cryptographic key types
 */
typedef enum {
    KEY_TYPE_SYMMETRIC,   // Symmetric key (e.g., AES)
    KEY_TYPE_KYBER,       // Kyber key (post-quantum KEM)
    KEY_TYPE_FALCON       // Falcon key (post-quantum signatures)
} key_type_t;

/**
 * Combined key reference for unified key management
 */
typedef struct {
    key_type_t type;
    uint8_t* key_id;      // Unique identifier for this key
    size_t key_id_size;
    uint64_t creation_time;
    uint64_t expiration_time;
    union {
        struct {
            uint8_t* key;
            size_t key_size;
        } symmetric;
        kyber_keypair_t kyber;
        falcon_keypair_t falcon;
    } key_data;
} crypto_key_t;

/**
 * Initialization parameters for the crypto adapter
 */
typedef struct {
    bool use_pq_crypto;   // Whether to use post-quantum cryptography
    bool use_hybrid;      // Whether to use hybrid cryptography (classical + PQ)
    const char* key_storage_path;  // Path for key storage (or NULL for in-memory only)
} crypto_adapter_params_t;

/**
 * Initialize the cryptographic adapter
 * 
 * @param params Initialization parameters
 * @return 0 on success, error code otherwise
 */
int crypto_adapter_init(const crypto_adapter_params_t* params);

/**
 * Generate a new cryptographic key
 * 
 * @param key_type Type of key to generate
 * @param key Pointer to crypto_key_t structure to receive the key
 * @param expires_in_seconds Time until key expiration (0 for no expiration)
 * @return 0 on success, error code otherwise
 */
int crypto_generate_key(key_type_t key_type, crypto_key_t* key, uint64_t expires_in_seconds);

/**
 * Sign a message using a Falcon key with post-quantum security
 * 
 * @param signature Buffer to receive the signature
 * @param signature_len Pointer to receive the signature length
 * @param message Message to sign
 * @param message_len Length of the message
 * @param key Falcon key to use for signing
 * @return 0 on success, error code otherwise
 */
int crypto_sign_message(
    uint8_t* signature,
    size_t* signature_len,
    const uint8_t* message,
    size_t message_len,
    const crypto_key_t* key
);

/**
 * Verify a signature using a Falcon public key
 * 
 * @param signature Signature to verify
 * @param signature_len Length of the signature
 * @param message Message that was signed
 * @param message_len Length of the message
 * @param key Falcon key containing the public key for verification
 * @return 1 if valid, 0 if invalid, negative on error
 */
int crypto_verify_signature(
    const uint8_t* signature,
    size_t signature_len,
    const uint8_t* message,
    size_t message_len,
    const crypto_key_t* key
);

/**
 * Establish a shared key using Kyber key encapsulation
 * 
 * @param shared_secret Buffer to receive the shared secret
 * @param shared_secret_len Pointer to receive the shared secret length
 * @param ciphertext Buffer to receive the ciphertext (NULL if not needed)
 * @param ciphertext_len Pointer to receive the ciphertext length (NULL if not needed)
 * @param recipient_key Kyber key of the recipient
 * @return 0 on success, error code otherwise
 */
int crypto_establish_key(
    uint8_t* shared_secret,
    size_t* shared_secret_len,
    uint8_t* ciphertext,
    size_t* ciphertext_len,
    const crypto_key_t* recipient_key
);

/**
 * Receive a shared key using Kyber key decapsulation
 * 
 * @param shared_secret Buffer to receive the shared secret
 * @param shared_secret_len Pointer to receive the shared secret length
 * @param ciphertext The ciphertext from the sender
 * @param ciphertext_len Length of the ciphertext
 * @param recipient_key Kyber key of the recipient (must include secret key)
 * @return 0 on success, error code otherwise
 */
int crypto_receive_key(
    uint8_t* shared_secret,
    size_t* shared_secret_len,
    const uint8_t* ciphertext,
    size_t ciphertext_len,
    const crypto_key_t* recipient_key
);

/**
 * Generate a zero-knowledge proof with post-quantum security
 * This combines the existing QZKP with Falcon signatures for additional security
 * 
 * @param proof Buffer to receive the proof
 * @param secret The secret to prove knowledge of
 * @param secret_size Size of the secret
 * @param public_input Public input for the proof
 * @param public_input_size Size of public input
 * @param key Falcon key for signing the proof
 * @return 0 on success, error code otherwise
 */
int crypto_generate_zkproof(
    qzkp_proof_t** proof,
    const void* secret,
    size_t secret_size,
    const void* public_input,
    size_t public_input_size,
    const crypto_key_t* key
);

/**
 * Verify a zero-knowledge proof with post-quantum security
 * 
 * @param proof The proof to verify
 * @param public_input Public input for verification
 * @param public_input_size Size of public input
 * @param key Falcon key for verifying the proof signature
 * @param params Verification parameters
 * @return 1 if valid, 0 if invalid, negative on error
 */
int crypto_verify_zkproof(
    const qzkp_proof_t* proof,
    const void* public_input,
    size_t public_input_size,
    const crypto_key_t* key,
    const qzkp_verify_params_t* params
);

/**
 * Free resources associated with a key
 * 
 * @param key Key to free
 */
void crypto_free_key(crypto_key_t* key);

/**
 * Clean up the cryptographic adapter
 */
void crypto_adapter_cleanup(void);

#endif /* CRYPTO_ADAPTER_H */
