/**
 * hydra_cgo.h
 * 
 * CGO-friendly interface for Hydra News cryptographic library
 */

#ifndef HYDRA_CGO_H
#define HYDRA_CGO_H

#ifdef __cplusplus
extern "C" {
#endif

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

/* Key types for CGO - using enum to avoid Go keywords */
typedef enum {
    KEY_TYPE_SYMMETRIC = 0,
    KEY_TYPE_KYBER = 1,
    KEY_TYPE_FALCON = 2
} hydra_key_type_t;

/* Constants for key sizes */
#define HYDRA_KYBER_PUBLIC_KEY_BYTES 1184
#define HYDRA_KYBER_SECRET_KEY_BYTES 2400
#define HYDRA_KYBER_CIPHERTEXT_BYTES 1088
#define HYDRA_KYBER_SHARED_SECRET_BYTES 32

#define HYDRA_FALCON_PUBLIC_KEY_BYTES 897
#define HYDRA_FALCON_SECRET_KEY_BYTES 1281
#define HYDRA_FALCON_SIGNATURE_MAX_BYTES 666

/**
 * Initialize all crypto libraries
 * 
 * @return 0 on success, error code otherwise
 */
int hydra_init(void);

/**
 * Clean up all crypto libraries
 */
void hydra_cleanup(void);

/**
 * Create a geolocation commitment
 * 
 * @param latitude Latitude coordinate
 * @param longitude Longitude coordinate
 * @param country_code Country code string
 * @param region_code Region code string
 * @param output Buffer to receive the commitment (must be at least 32 bytes)
 * @return 0 on success, error code otherwise
 */
int hydra_create_geolocation_commitment(
    double latitude,
    double longitude,
    const char* country_code,
    const char* region_code,
    uint8_t* output
);

/**
 * Generate a Kyber key pair
 * 
 * @param public_key Buffer to receive the public key (must be at least HYDRA_KYBER_PUBLIC_KEY_BYTES)
 * @param secret_key Buffer to receive the secret key (must be at least HYDRA_KYBER_SECRET_KEY_BYTES)
 * @return 0 on success, error code otherwise
 */
int hydra_generate_kyber_key(
    uint8_t* public_key,
    uint8_t* secret_key
);

/**
 * Generate a Falcon key pair
 * 
 * @param public_key Buffer to receive the public key (must be at least HYDRA_FALCON_PUBLIC_KEY_BYTES)
 * @param secret_key Buffer to receive the secret key (must be at least HYDRA_FALCON_SECRET_KEY_BYTES)
 * @return 0 on success, error code otherwise
 */
int hydra_generate_falcon_key(
    uint8_t* public_key,
    uint8_t* secret_key
);

/**
 * Sign a message using Falcon
 * 
 * @param message Message to sign
 * @param message_len Length of the message in bytes
 * @param secret_key Falcon secret key
 * @param signature Buffer to receive the signature (must be at least HYDRA_FALCON_SIGNATURE_MAX_BYTES)
 * @param signature_len Pointer to receive the actual signature length
 * @return 0 on success, error code otherwise
 */
int hydra_sign_message(
    const uint8_t* message,
    size_t message_len,
    const uint8_t* secret_key,
    uint8_t* signature,
    size_t* signature_len
);

/**
 * Verify a message signature using Falcon
 * 
 * @param message Message that was signed
 * @param message_len Length of the message in bytes
 * @param signature The signature to verify
 * @param signature_len Length of the signature in bytes
 * @param public_key Falcon public key
 * @return 1 if valid, 0 if invalid, negative value on error
 */
int hydra_verify_signature(
    const uint8_t* message,
    size_t message_len,
    const uint8_t* signature,
    size_t signature_len,
    const uint8_t* public_key
);

/**
 * Create a shared key using Kyber key encapsulation
 * 
 * @param public_key Recipient's Kyber public key
 * @param shared_secret Buffer to receive the shared secret (must be at least 32 bytes)
 * @param ciphertext Buffer to receive the ciphertext (must be at least HYDRA_KYBER_CIPHERTEXT_BYTES)
 * @return 0 on success, error code otherwise
 */
int hydra_establish_shared_key(
    const uint8_t* public_key,
    uint8_t* shared_secret,
    uint8_t* ciphertext
);

/**
 * Decrypt a shared key using Kyber key decapsulation
 * 
 * @param secret_key Recipient's Kyber secret key
 * @param ciphertext The ciphertext from the sender
 * @param shared_secret Buffer to receive the shared secret (must be at least 32 bytes)
 * @return 0 on success, error code otherwise
 */
int hydra_receive_shared_key(
    const uint8_t* secret_key,
    const uint8_t* ciphertext,
    uint8_t* shared_secret
);

/**
 * Generate a zero-knowledge proof
 * 
 * @param secret Secret data
 * @param secret_len Length of secret data in bytes
 * @param public_input Public data
 * @param public_len Length of public data in bytes
 * @param proof_out Buffer to receive the proof (must be big enough)
 * @param proof_len Pointer to receive the proof length
 * @return 0 on success, error code otherwise
 */
int hydra_generate_zkproof(
    const uint8_t* secret,
    size_t secret_len,
    const uint8_t* public_input,
    size_t public_len,
    uint8_t* proof_out,
    size_t* proof_len
);

/**
 * Verify a zero-knowledge proof
 * 
 * @param proof The proof to verify
 * @param proof_len Length of the proof in bytes
 * @param public_input Public data
 * @param public_len Length of public data in bytes
 * @return 1 if valid, 0 if invalid, negative value on error
 */
int hydra_verify_zkproof(
    const uint8_t* proof,
    size_t proof_len,
    const uint8_t* public_input,
    size_t public_len
);

/**
 * Create a logical entanglement of multiple data items
 * 
 * @param data_items Array of data pointers
 * @param data_lengths Array of data lengths
 * @param count Number of data items
 * @param output Buffer to receive the entanglement hash (must be at least 32 bytes)
 * @return 0 on success, error code otherwise
 */
int hydra_create_entanglement(
    const uint8_t** data_items,
    const size_t* data_lengths,
    size_t count,
    uint8_t* output
);

/**
 * Verify if data items match an entanglement hash
 * 
 * @param data_items Array of data pointers
 * @param data_lengths Array of data lengths
 * @param count Number of data items
 * @param entanglement_hash The entanglement hash to verify against
 * @return 1 if valid, 0 if invalid, negative value on error
 */
int hydra_verify_entanglement(
    const uint8_t** data_items,
    const size_t* data_lengths,
    size_t count,
    const uint8_t* entanglement_hash
);

#ifdef __cplusplus
}
#endif

#endif /* HYDRA_CGO_H */
