/**
 * key_management.c
 * 
 * Implementation of the key management system for Hydra News
 * Provides forward secrecy and key rotation mechanisms
 */

#include "key_management.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <openssl/rand.h>
#include <openssl/evp.h>
#include <openssl/sha.h>
#include <openssl/aes.h>
#include <openssl/err.h>

// Include Kyber for post-quantum key encapsulation
// Note: In a real implementation, this would include the actual Kyber headers
#include "../postquantum/kyber.h"

// Include Falcon for post-quantum signatures
// Note: In a real implementation, this would include the actual Falcon headers
#include "../postquantum/falcon.h"

// Maximum number of keys to store
#define MAX_KEYS 1024

// Default rotation interval (30 days in seconds)
#define DEFAULT_ROTATION_INTERVAL (30 * 24 * 60 * 60)

// Key storage structure
typedef struct {
    key_container_t keys[MAX_KEYS];
    size_t key_count;
    char storage_path[256];
    bool initialized;
} key_storage_t;

// Global key storage
static key_storage_t g_key_storage = {
    .key_count = 0,
    .initialized = false
};

// Forward declarations of helper functions
static int generate_key_id(char* key_id, size_t key_id_size);
static int save_keys_to_storage(void);
static int load_keys_from_storage(void);
static key_container_t* find_key_by_id(const char* key_id);
static key_container_t* find_active_key_by_purpose(key_purpose_t purpose);
static int generate_key_material(key_type_t type, uint8_t** key_material, size_t* key_material_size);
static int secure_wipe(void* data, size_t size);
static const char* key_type_to_string(key_type_t type);
static const char* key_purpose_to_string(key_purpose_t purpose);

/**
 * Initialize the key management system
 */
int key_mgmt_init(const char* storage_path) {
    // Check if already initialized
    if (g_key_storage.initialized) {
        return 0; // Already initialized
    }
    
    // Initialize OpenSSL
    OpenSSL_add_all_algorithms();
    
    // Initialize key storage
    memset(&g_key_storage, 0, sizeof(key_storage_t));
    
    if (storage_path != NULL) {
        strncpy(g_key_storage.storage_path, storage_path, sizeof(g_key_storage.storage_path) - 1);
        g_key_storage.storage_path[sizeof(g_key_storage.storage_path) - 1] = '\0';
        
        // Load keys from storage
        if (load_keys_from_storage() != 0) {
            fprintf(stderr, "Warning: Failed to load keys from storage, initializing empty key storage\n");
        }
    }
    
    g_key_storage.initialized = true;
    return 0;
}

/**
 * Create a new key
 */
int key_mgmt_create_key(key_type_t type, key_purpose_t purpose, char* key_id) {
    // Check if initialized
    if (!g_key_storage.initialized) {
        return -1; // Not initialized
    }
    
    // Check if we have space for a new key
    if (g_key_storage.key_count >= MAX_KEYS) {
        return -2; // No space for new key
    }
    
    // Generate a unique key ID
    char new_key_id[64];
    if (generate_key_id(new_key_id, sizeof(new_key_id)) != 0) {
        return -3; // Failed to generate key ID
    }
    
    // Generate key material
    uint8_t* key_material = NULL;
    size_t key_material_size = 0;
    if (generate_key_material(type, &key_material, &key_material_size) != 0) {
        return -4; // Failed to generate key material
    }
    
    // Create key container
    key_container_t* key = &g_key_storage.keys[g_key_storage.key_count];
    memset(key, 0, sizeof(key_container_t));
    
    // Set metadata
    strncpy(key->metadata.key_id, new_key_id, sizeof(key->metadata.key_id) - 1);
    key->metadata.key_id[sizeof(key->metadata.key_id) - 1] = '\0';
    key->metadata.type = type;
    key->metadata.purpose = purpose;
    key->metadata.creation_time = time(NULL);
    key->metadata.rotation_time = key->metadata.creation_time;
    key->metadata.expiration_time = key->metadata.creation_time + DEFAULT_ROTATION_INTERVAL;
    key->metadata.version = 1;
    key->metadata.is_active = true;
    
    // Set key material
    key->key_material = key_material;
    key->key_material_size = key_material_size;
    
    // Increment key count
    g_key_storage.key_count++;
    
    // Save keys to storage if path is set
    if (g_key_storage.storage_path[0] != '\0') {
        save_keys_to_storage();
    }
    
    // Copy key ID to output parameter
    if (key_id != NULL) {
        strncpy(key_id, new_key_id, 64);
    }
    
    printf("Created new %s key for %s purpose, ID: %s\n", 
           key_type_to_string(type), 
           key_purpose_to_string(purpose), 
           new_key_id);
    
    return 0;
}

/**
 * Get key metadata by ID
 */
int key_mgmt_get_key_metadata(const char* key_id, key_metadata_t* metadata) {
    // Check if initialized
    if (!g_key_storage.initialized) {
        return -1; // Not initialized
    }
    
    // Find key by ID
    key_container_t* key = find_key_by_id(key_id);
    if (key == NULL) {
        return -2; // Key not found
    }
    
    // Copy metadata
    if (metadata != NULL) {
        memcpy(metadata, &key->metadata, sizeof(key_metadata_t));
    }
    
    return 0;
}

/**
 * Get active key for a specific purpose
 */
int key_mgmt_get_active_key(key_purpose_t purpose, char* key_id) {
    // Check if initialized
    if (!g_key_storage.initialized) {
        return -1; // Not initialized
    }
    
    // Find active key by purpose
    key_container_t* key = find_active_key_by_purpose(purpose);
    if (key == NULL) {
        return -2; // No active key found for purpose
    }
    
    // Copy key ID to output parameter
    if (key_id != NULL) {
        strncpy(key_id, key->metadata.key_id, 64);
    }
    
    return 0;
}

/**
 * Rotate a key by ID
 */
int key_mgmt_rotate_key(const char* key_id) {
    // Check if initialized
    if (!g_key_storage.initialized) {
        return -1; // Not initialized
    }
    
    // Find key by ID
    key_container_t* key = find_key_by_id(key_id);
    if (key == NULL) {
        return -2; // Key not found
    }
    
    // Generate new key material
    uint8_t* key_material = NULL;
    size_t key_material_size = 0;
    if (generate_key_material(key->metadata.type, &key_material, &key_material_size) != 0) {
        return -3; // Failed to generate key material
    }
    
    // Securely wipe old key material
    secure_wipe(key->key_material, key->key_material_size);
    
    // Free old key material
    free(key->key_material);
    
    // Update metadata
    key->metadata.rotation_time = time(NULL);
    key->metadata.expiration_time = key->metadata.rotation_time + DEFAULT_ROTATION_INTERVAL;
    key->metadata.version++;
    
    // Set new key material
    key->key_material = key_material;
    key->key_material_size = key_material_size;
    
    // Save keys to storage if path is set
    if (g_key_storage.storage_path[0] != '\0') {
        save_keys_to_storage();
    }
    
    printf("Rotated %s key for %s purpose, ID: %s, new version: %u\n", 
           key_type_to_string(key->metadata.type), 
           key_purpose_to_string(key->metadata.purpose), 
           key->metadata.key_id,
           key->metadata.version);
    
    return 0;
}

/**
 * Set key rotation policy for a key
 */
int key_mgmt_set_rotation_policy(const char* key_id, const key_rotation_policy_t* policy) {
    // In a full implementation, this would store the policy and apply it
    // For this simplified version, we'll just acknowledge the call
    return 0;
}

/**
 * Export key in encrypted form (for backup)
 */
int key_mgmt_export_key(const char* key_id, const char* password, 
                       uint8_t* output, size_t output_size, size_t* bytes_written) {
    // Check if initialized
    if (!g_key_storage.initialized) {
        return -1; // Not initialized
    }
    
    // Find key by ID
    key_container_t* key = find_key_by_id(key_id);
    if (key == NULL) {
        return -2; // Key not found
    }
    
    // Check output buffer size
    size_t required_size = sizeof(key_metadata_t) + key->key_material_size + 128; // Additional space for encryption overhead
    if (output_size < required_size) {
        return -3; // Output buffer too small
    }
    
    // In a full implementation, this would:
    // 1. Derive an encryption key from the password
    // 2. Encrypt the key material with the derived key
    // 3. Include metadata and authentication tag
    
    // For this simplified version, we'll just copy the metadata
    memcpy(output, &key->metadata, sizeof(key_metadata_t));
    
    // Set bytes written
    if (bytes_written != NULL) {
        *bytes_written = sizeof(key_metadata_t);
    }
    
    return 0;
}

/**
 * Import key from encrypted form
 */
int key_mgmt_import_key(const char* password, const uint8_t* input, 
                       size_t input_size, char* key_id) {
    // Check if initialized
    if (!g_key_storage.initialized) {
        return -1; // Not initialized
    }
    
    // Check if we have space for a new key
    if (g_key_storage.key_count >= MAX_KEYS) {
        return -2; // No space for new key
    }
    
    // In a full implementation, this would:
    // 1. Derive an encryption key from the password
    // 2. Decrypt the key material with the derived key
    // 3. Verify authentication tag
    // 4. Extract metadata and key material
    
    // For this simplified version, we'll just acknowledge the call
    
    // Copy key ID to output parameter if provided
    if (key_id != NULL) {
        strncpy(key_id, "imported-key", 64);
    }
    
    return 0;
}

/**
 * Encrypt data using a key
 */
int key_mgmt_encrypt(const char* key_id, const uint8_t* plaintext, size_t plaintext_size,
                    uint8_t* output, size_t output_size, size_t* bytes_written) {
    // Check if initialized
    if (!g_key_storage.initialized) {
        return -1; // Not initialized
    }
    
    // Find key by ID
    key_container_t* key = find_key_by_id(key_id);
    if (key == NULL) {
        return -2; // Key not found
    }
    
    // Check if key type is suitable for encryption
    if (key->metadata.type != KEY_TYPE_SYMMETRIC_AES && 
        key->metadata.type != KEY_TYPE_ASYMMETRIC_KYBER &&
        key->metadata.type != KEY_TYPE_HYBRID) {
        return -3; // Key type not suitable
    }
    
    // Check output buffer size (accounting for IV and authentication tag)
    size_t required_size = plaintext_size + 32; // Space for IV and tag
    if (output_size < required_size) {
        return -4; // Output buffer too small
    }
    
    // In a full implementation, this would:
    // 1. Generate a random IV
    // 2. Set up encryption context with the key
    // 3. Encrypt the plaintext
    // 4. Include the IV and authentication tag in the output
    
    // For this simplified version, we'll just copy the data
    memcpy(output, plaintext, plaintext_size);
    
    // Set bytes written
    if (bytes_written != NULL) {
        *bytes_written = plaintext_size;
    }
    
    return 0;
}

/**
 * Decrypt data using a key
 */
int key_mgmt_decrypt(const char* key_id, const uint8_t* ciphertext, size_t ciphertext_size,
                    uint8_t* output, size_t output_size, size_t* bytes_written) {
    // Check if initialized
    if (!g_key_storage.initialized) {
        return -1; // Not initialized
    }
    
    // Find key by ID
    key_container_t* key = find_key_by_id(key_id);
    if (key == NULL) {
        return -2; // Key not found
    }
    
    // Check if key type is suitable for decryption
    if (key->metadata.type != KEY_TYPE_SYMMETRIC_AES && 
        key->metadata.type != KEY_TYPE_ASYMMETRIC_KYBER &&
        key->metadata.type != KEY_TYPE_HYBRID) {
        return -3; // Key type not suitable
    }
    
    // Check output buffer size
    if (output_size < ciphertext_size) {
        return -4; // Output buffer too small
    }
    
    // In a full implementation, this would:
    // 1. Extract the IV from the ciphertext
    // 2. Set up decryption context with the key
    // 3. Decrypt the ciphertext
    // 4. Verify the authentication tag
    
    // For this simplified version, we'll just copy the data
    memcpy(output, ciphertext, ciphertext_size);
    
    // Set bytes written
    if (bytes_written != NULL) {
        *bytes_written = ciphertext_size;
    }
    
    return 0;
}

/**
 * Generate an ephemeral session key with forward secrecy
 */
int key_mgmt_generate_ephemeral_key(key_purpose_t purpose, uint32_t lifetime_seconds, char* key_id) {
    // Check if initialized
    if (!g_key_storage.initialized) {
        return -1; // Not initialized
    }
    
    // Check if we have space for a new key
    if (g_key_storage.key_count >= MAX_KEYS) {
        return -2; // No space for new key
    }
    
    // Generate a unique key ID
    char new_key_id[64];
    if (generate_key_id(new_key_id, sizeof(new_key_id)) != 0) {
        return -3; // Failed to generate key ID
    }
    
    // Generate key material for an AES key
    uint8_t* key_material = NULL;
    size_t key_material_size = 0;
    if (generate_key_material(KEY_TYPE_SYMMETRIC_AES, &key_material, &key_material_size) != 0) {
        return -4; // Failed to generate key material
    }
    
    // Create key container
    key_container_t* key = &g_key_storage.keys[g_key_storage.key_count];
    memset(key, 0, sizeof(key_container_t));
    
    // Set metadata
    strncpy(key->metadata.key_id, new_key_id, sizeof(key->metadata.key_id) - 1);
    key->metadata.key_id[sizeof(key->metadata.key_id) - 1] = '\0';
    key->metadata.type = KEY_TYPE_SYMMETRIC_AES;
    key->metadata.purpose = purpose;
    key->metadata.creation_time = time(NULL);
    key->metadata.rotation_time = key->metadata.creation_time;
    key->metadata.expiration_time = key->metadata.creation_time + lifetime_seconds;
    key->metadata.version = 1;
    key->metadata.is_active = true;
    
    // Set key material
    key->key_material = key_material;
    key->key_material_size = key_material_size;
    
    // Increment key count
    g_key_storage.key_count++;
    
    // Copy key ID to output parameter
    if (key_id != NULL) {
        strncpy(key_id, new_key_id, 64);
    }
    
    printf("Created new ephemeral key for %s purpose, ID: %s, lifetime: %u seconds\n", 
           key_purpose_to_string(purpose), 
           new_key_id,
           lifetime_seconds);
    
    return 0;
}

/**
 * Establish a shared key with a peer using post-quantum key exchange
 */
int key_mgmt_establish_shared_key(const uint8_t* peer_public_key, size_t peer_public_key_size, 
                                 char* shared_key_id) {
    // Check if initialized
    if (!g_key_storage.initialized) {
        return -1; // Not initialized
    }
    
    // Check if we have space for a new key
    if (g_key_storage.key_count >= MAX_KEYS) {
        return -2; // No space for new key
    }
    
    // Generate a unique key ID
    char new_key_id[64];
    if (generate_key_id(new_key_id, sizeof(new_key_id)) != 0) {
        return -3; // Failed to generate key ID
    }
    
    // In a full implementation, this would use Kyber to establish a shared key
    
    // For this simplified version, we'll just create a new AES key
    uint8_t* key_material = NULL;
    size_t key_material_size = 0;
    if (generate_key_material(KEY_TYPE_SYMMETRIC_AES, &key_material, &key_material_size) != 0) {
        return -4; // Failed to generate key material
    }
    
    // Create key container
    key_container_t* key = &g_key_storage.keys[g_key_storage.key_count];
    memset(key, 0, sizeof(key_container_t));
    
    // Set metadata
    strncpy(key->metadata.key_id, new_key_id, sizeof(key->metadata.key_id) - 1);
    key->metadata.key_id[sizeof(key->metadata.key_id) - 1] = '\0';
    key->metadata.type = KEY_TYPE_SYMMETRIC_AES;
    key->metadata.purpose = KEY_PURPOSE_EPHEMERAL;
    key->metadata.creation_time = time(NULL);
    key->metadata.rotation_time = key->metadata.creation_time;
    key->metadata.expiration_time = key->metadata.creation_time + (60 * 60); // 1 hour
    key->metadata.version = 1;
    key->metadata.is_active = true;
    
    // Set key material
    key->key_material = key_material;
    key->key_material_size = key_material_size;
    
    // Increment key count
    g_key_storage.key_count++;
    
    // Copy key ID to output parameter
    if (shared_key_id != NULL) {
        strncpy(shared_key_id, new_key_id, 64);
    }
    
    printf("Established shared key ID: %s\n", new_key_id);
    
    return 0;
}

/**
 * Revoke a key by ID
 */
int key_mgmt_revoke_key(const char* key_id) {
    // Check if initialized
    if (!g_key_storage.initialized) {
        return -1; // Not initialized
    }
    
    // Find key by ID
    key_container_t* key = find_key_by_id(key_id);
    if (key == NULL) {
        return -2; // Key not found
    }
    
    // Mark key as inactive
    key->metadata.is_active = false;
    
    printf("Revoked key ID: %s\n", key_id);
    
    return 0;
}

/**
 * Clean up the key management system
 */
int key_mgmt_cleanup(void) {
    // Check if initialized
    if (!g_key_storage.initialized) {
        return 0; // Nothing to do
    }
    
    // Securely wipe and free all key material
    for (size_t i = 0; i < g_key_storage.key_count; i++) {
        key_container_t* key = &g_key_storage.keys[i];
        
        // Securely wipe key material
        secure_wipe(key->key_material, key->key_material_size);
        
        // Free key material
        free(key->key_material);
        
        // Clear metadata
        memset(&key->metadata, 0, sizeof(key_metadata_t));
    }
    
    // Reset key count
    g_key_storage.key_count = 0;
    
    // Clear storage path
    memset(g_key_storage.storage_path, 0, sizeof(g_key_storage.storage_path));
    
    // Mark as uninitialized
    g_key_storage.initialized = false;
    
    return 0;
}

/**
 * Generate a unique key ID
 */
static int generate_key_id(char* key_id, size_t key_id_size) {
    // Check parameters
    if (key_id == NULL || key_id_size < 64) {
        return -1;
    }
    
    // Generate random data
    uint8_t random_data[32];
    if (RAND_bytes(random_data, sizeof(random_data)) != 1) {
        return -2;
    }
    
    // Format as hex string
    for (size_t i = 0; i < 32; i++) {
        snprintf(key_id + (i * 2), 3, "%02x", random_data[i]);
    }
    
    return 0;
}

/**
 * Save keys to storage
 */
static int save_keys_to_storage(void) {
    // In a real implementation, this would encrypt and save the keys to disk
    // For this simplified version, we'll just acknowledge the call
    
    return 0;
}

/**
 * Load keys from storage
 */
static int load_keys_from_storage(void) {
    // In a real implementation, this would load and decrypt the keys from disk
    // For this simplified version, we'll just acknowledge the call
    
    return 0;
}

/**
 * Find a key by ID
 */
static key_container_t* find_key_by_id(const char* key_id) {
    // Check parameters
    if (key_id == NULL) {
        return NULL;
    }
    
    // Search for key
    for (size_t i = 0; i < g_key_storage.key_count; i++) {
        key_container_t* key = &g_key_storage.keys[i];
        
        if (strcmp(key->metadata.key_id, key_id) == 0) {
            return key;
        }
    }
    
    return NULL;
}

/**
 * Find an active key by purpose
 */
static key_container_t* find_active_key_by_purpose(key_purpose_t purpose) {
    // Search for key
    for (size_t i = 0; i < g_key_storage.key_count; i++) {
        key_container_t* key = &g_key_storage.keys[i];
        
        if (key->metadata.purpose == purpose && key->metadata.is_active) {
            // Check if expired
            time_t now = time(NULL);
            if (now < key->metadata.expiration_time) {
                return key;
            }
        }
    }
    
    return NULL;
}

/**
 * Generate key material for a specific key type
 */
static int generate_key_material(key_type_t type, uint8_t** key_material, size_t* key_material_size) {
    // Check parameters
    if (key_material == NULL || key_material_size == NULL) {
        return -1;
    }
    
    // Determine key size based on type
    size_t size = 0;
    switch (type) {
        case KEY_TYPE_SYMMETRIC_AES:
            size = 32; // 256-bit AES key
            break;
        case KEY_TYPE_ASYMMETRIC_KYBER:
            size = 1632; // Kyber-768 key size
            break;
        case KEY_TYPE_SIGNATURE_FALCON:
            size = 1281; // Falcon-512 key size
            break;
        case KEY_TYPE_HYBRID:
            size = 1632 + 32; // Kyber + AES
            break;
        default:
            return -2; // Unknown key type
    }
    
    // Allocate memory for key material
    uint8_t* material = malloc(size);
    if (material == NULL) {
        return -3; // Memory allocation failed
    }
    
    // Generate random data for key material
    if (RAND_bytes(material, size) != 1) {
        free(material);
        return -4; // Failed to generate random data
    }
    
    // Set output parameters
    *key_material = material;
    *key_material_size = size;
    
    return 0;
}

/**
 * Securely wipe memory
 */
static int secure_wipe(void* data, size_t size) {
    // Check parameters
    if (data == NULL || size == 0) {
        return -1;
    }
    
    // Use volatile pointer to prevent optimization
    volatile uint8_t* p = (volatile uint8_t*)data;
    
    // Overwrite with zeros
    for (size_t i = 0; i < size; i++) {
        p[i] = 0;
    }
    
    return 0;
}

/**
 * Convert key type to string
 */
static const char* key_type_to_string(key_type_t type) {
    switch (type) {
        case KEY_TYPE_SYMMETRIC_AES:
            return "AES";
        case KEY_TYPE_ASYMMETRIC_KYBER:
            return "Kyber";
        case KEY_TYPE_SIGNATURE_FALCON:
            return "Falcon";
        case KEY_TYPE_HYBRID:
            return "Hybrid";
        default:
            return "Unknown";
    }
}

/**
 * Convert key purpose to string
 */
static const char* key_purpose_to_string(key_purpose_t purpose) {
    switch (purpose) {
        case KEY_PURPOSE_CONTENT_ENCRYPTION:
            return "Content Encryption";
        case KEY_PURPOSE_IDENTITY:
            return "Identity";
        case KEY_PURPOSE_SOURCE_PROTECTION:
            return "Source Protection";
        case KEY_PURPOSE_EPHEMERAL:
            return "Ephemeral";
        case KEY_PURPOSE_CONSENSUS:
            return "Consensus";
        default:
            return "Unknown";
    }
}
