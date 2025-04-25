/**
 * key_management.h
 * 
 * Key management system for Hydra News with forward secrecy and key rotation
 * Features post-quantum secure key handling and rotation mechanisms
 */

#ifndef KEY_MANAGEMENT_H
#define KEY_MANAGEMENT_H

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>
#include <time.h>

/**
 * Key types supported by the key management system
 */
typedef enum {
    KEY_TYPE_SYMMETRIC_AES,      // AES symmetric key
    KEY_TYPE_ASYMMETRIC_KYBER,   // Kyber post-quantum KEM
    KEY_TYPE_SIGNATURE_FALCON,   // Falcon post-quantum signature
    KEY_TYPE_HYBRID              // Hybrid classical/post-quantum
} key_type_t;

/**
 * Key usage purposes
 */
typedef enum {
    KEY_PURPOSE_CONTENT_ENCRYPTION,  // For encrypting content
    KEY_PURPOSE_IDENTITY,            // For identity verification
    KEY_PURPOSE_SOURCE_PROTECTION,   // For protecting source identity
    KEY_PURPOSE_EPHEMERAL,           // Short-lived session keys
    KEY_PURPOSE_CONSENSUS            // For consensus operations
} key_purpose_t;

/**
 * Key metadata structure
 */
typedef struct {
    char key_id[64];             // Unique identifier for the key
    key_type_t type;             // Type of key
    key_purpose_t purpose;       // Purpose of the key
    time_t creation_time;        // When the key was created
    time_t rotation_time;        // When the key was last rotated
    time_t expiration_time;      // When the key expires
    uint32_t version;            // Key version
    bool is_active;              // Whether the key is currently active
} key_metadata_t;

/**
 * Key container structure for storing key material
 */
typedef struct {
    key_metadata_t metadata;     // Key metadata
    uint8_t* key_material;       // The actual key material
    size_t key_material_size;    // Size of the key material in bytes
} key_container_t;

/**
 * Key rotation policy structure
 */
typedef struct {
    time_t rotation_interval;    // Time interval between rotations
    uint32_t max_usage_count;    // Maximum number of uses before rotation
    bool rotate_on_compromise;   // Whether to rotate upon suspected compromise
} key_rotation_policy_t;

/**
 * Initialize the key management system
 * 
 * @param storage_path Path to store key material (or NULL for in-memory only)
 * @return 0 on success, error code otherwise
 */
int key_mgmt_init(const char* storage_path);

/**
 * Create a new key
 * 
 * @param type Type of key to create
 * @param purpose Purpose of the key
 * @param key_id Buffer to store the generated key ID (must be at least 64 bytes)
 * @return 0 on success, error code otherwise
 */
int key_mgmt_create_key(key_type_t type, key_purpose_t purpose, char* key_id);

/**
 * Get key metadata by ID
 * 
 * @param key_id ID of the key to retrieve
 * @param metadata Pointer to store the key metadata
 * @return 0 on success, error code otherwise
 */
int key_mgmt_get_key_metadata(const char* key_id, key_metadata_t* metadata);

/**
 * Get active key for a specific purpose
 * 
 * @param purpose Purpose of the key
 * @param key_id Buffer to store the key ID (must be at least 64 bytes)
 * @return 0 on success, error code otherwise
 */
int key_mgmt_get_active_key(key_purpose_t purpose, char* key_id);

/**
 * Rotate a key by ID
 * 
 * @param key_id ID of the key to rotate
 * @return 0 on success, error code otherwise
 */
int key_mgmt_rotate_key(const char* key_id);

/**
 * Set key rotation policy for a key
 * 
 * @param key_id ID of the key
 * @param policy Rotation policy to set
 * @return 0 on success, error code otherwise
 */
int key_mgmt_set_rotation_policy(const char* key_id, const key_rotation_policy_t* policy);

/**
 * Export key in encrypted form (for backup)
 * 
 * @param key_id ID of the key to export
 * @param password Password to encrypt the key with
 * @param output Buffer to store the exported key
 * @param output_size Size of the output buffer
 * @param bytes_written Pointer to store the number of bytes written
 * @return 0 on success, error code otherwise
 */
int key_mgmt_export_key(const char* key_id, const char* password, 
                       uint8_t* output, size_t output_size, size_t* bytes_written);

/**
 * Import key from encrypted form
 * 
 * @param password Password to decrypt the key with
 * @param input Encrypted key data
 * @param input_size Size of the input data
 * @param key_id Buffer to store the imported key ID (must be at least 64 bytes)
 * @return 0 on success, error code otherwise
 */
int key_mgmt_import_key(const char* password, const uint8_t* input, 
                       size_t input_size, char* key_id);

/**
 * Encrypt data using a key
 * 
 * @param key_id ID of the key to use
 * @param plaintext Data to encrypt
 * @param plaintext_size Size of the plaintext data
 * @param output Buffer to store the encrypted data
 * @param output_size Size of the output buffer
 * @param bytes_written Pointer to store the number of bytes written
 * @return 0 on success, error code otherwise
 */
int key_mgmt_encrypt(const char* key_id, const uint8_t* plaintext, size_t plaintext_size,
                    uint8_t* output, size_t output_size, size_t* bytes_written);

/**
 * Decrypt data using a key
 * 
 * @param key_id ID of the key to use
 * @param ciphertext Data to decrypt
 * @param ciphertext_size Size of the ciphertext data
 * @param output Buffer to store the decrypted data
 * @param output_size Size of the output buffer
 * @param bytes_written Pointer to store the number of bytes written
 * @return 0 on success, error code otherwise
 */
int key_mgmt_decrypt(const char* key_id, const uint8_t* ciphertext, size_t ciphertext_size,
                    uint8_t* output, size_t output_size, size_t* bytes_written);

/**
 * Generate an ephemeral session key with forward secrecy
 * 
 * @param purpose Purpose of the key
 * @param lifetime_seconds How long the key should be valid for
 * @param key_id Buffer to store the generated key ID (must be at least 64 bytes)
 * @return 0 on success, error code otherwise
 */
int key_mgmt_generate_ephemeral_key(key_purpose_t purpose, uint32_t lifetime_seconds, char* key_id);

/**
 * Establish a shared key with a peer using post-quantum key exchange
 * 
 * @param peer_public_key Public key of the peer
 * @param peer_public_key_size Size of the peer public key
 * @param shared_key_id Buffer to store the generated shared key ID (must be at least 64 bytes)
 * @return 0 on success, error code otherwise
 */
int key_mgmt_establish_shared_key(const uint8_t* peer_public_key, size_t peer_public_key_size, 
                                 char* shared_key_id);

/**
 * Revoke a key by ID
 * 
 * @param key_id ID of the key to revoke
 * @return 0 on success, error code otherwise
 */
int key_mgmt_revoke_key(const char* key_id);

/**
 * Clean up the key management system
 * 
 * @return 0 on success, error code otherwise
 */
int key_mgmt_cleanup(void);

#endif /* KEY_MANAGEMENT_H */
