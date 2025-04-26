/**
 * hydra_cgo.c
 * 
 * Implementation of the CGO-friendly interface for Hydra News
 */

#include "hydra_cgo.h"
#include "quantum_zkp.h"
#include "logical_entanglement.h"
#include "postquantum/kyber.h"
#include "postquantum/falcon.h"
#include "postquantum/crypto_adapter.h"
#include <string.h>
#include <stdlib.h>

/* Global initialization flag */
static bool hydra_initialized = false;

/**
 * Initialize all cryptographic modules
 */
int hydra_init(void) {
    if (hydra_initialized) {
        return 0;  // Already initialized
    }

    // Initialize QZKP
    int result = qzkp_init();
    if (result != 0) {
        return result;
    }

    // Initialize logical entanglement
    result = le_init();
    if (result != 0) {
        qzkp_cleanup();
        return result;
    }

    // Initialize Kyber
    result = kyber_init();
    if (result != 0) {
        le_cleanup();
        qzkp_cleanup();
        return result;
    }

    // Initialize Falcon
    result = falcon_init();
    if (result != 0) {
        kyber_cleanup();
        le_cleanup();
        qzkp_cleanup();
        return result;
    }

    // Initialize crypto adapter
    crypto_adapter_params_t params = {
        .use_pq_crypto = true,
        .use_hybrid = true,
        .key_storage_path = NULL
    };

    result = crypto_adapter_init(&params);
    if (result != 0) {
        falcon_cleanup();
        kyber_cleanup();
        le_cleanup();
        qzkp_cleanup();
        return result;
    }

    hydra_initialized = true;
    return 0;
}

/**
 * Clean up all cryptographic modules
 */
void hydra_cleanup(void) {
    if (!hydra_initialized) {
        return;  // Not initialized
    }

    // Clean up in reverse order of initialization
    crypto_adapter_cleanup();
    falcon_cleanup();
    kyber_cleanup();
    le_cleanup();
    qzkp_cleanup();

    hydra_initialized = false;
}

/**
 * Create a geolocation commitment
 */
int hydra_create_geolocation_commitment(
    double latitude,
    double longitude,
    const char* country_code,
    const char* region_code,
    uint8_t* output
) {
    if (!hydra_initialized || !country_code || !region_code || !output) {
        return -1;
    }

    // Create a location data buffer
    // Format: latitude(8) + longitude(8) + country_code + region_code
    size_t cc_len = strlen(country_code);
    size_t rc_len = strlen(region_code);
    size_t data_size = 16 + cc_len + rc_len;
    uint8_t* data = (uint8_t*)malloc(data_size);
    if (!data) {
        return -2;
    }

    // Copy latitude and longitude
    memcpy(data, &latitude, 8);
    memcpy(data + 8, &longitude, 8);

    // Copy country and region codes
    memcpy(data + 16, country_code, cc_len);
    memcpy(data + 16 + cc_len, region_code, rc_len);

    // Apply entanglement to create commitment
    void* states[1] = { data };
    uint8_t* commitment = qzkp_apply_entanglement(states, 1, data_size);
    if (!commitment) {
        free(data);
        return -3;
    }

    // Copy the commitment to the output buffer
    memcpy(output, commitment, 32);

    // Clean up
    free(commitment);
    free(data);

    return 0;
}

/**
 * Generate a Kyber key pair
 */
int hydra_generate_kyber_key(
    uint8_t* public_key,
    uint8_t* secret_key
) {
    if (!hydra_initialized || !public_key || !secret_key) {
        return -1;
    }

    // Generate Kyber keypair
    kyber_keypair_t keypair;
    int result = kyber_keygen(&keypair);
    if (result != 0) {
        return result;
    }

    // Copy keys to output buffers
    memcpy(public_key, keypair.public_key, KYBER_PUBLIC_KEY_BYTES);
    memcpy(secret_key, keypair.secret_key, KYBER_SECRET_KEY_BYTES);

    return 0;
}

/**
 * Generate a Falcon key pair
 */
int hydra_generate_falcon_key(
    uint8_t* public_key,
    uint8_t* secret_key
) {
    if (!hydra_initialized || !public_key || !secret_key) {
        return -1;
    }

    // Generate Falcon keypair
    falcon_keypair_t keypair;
    int result = falcon_keygen(&keypair);
    if (result != 0) {
        return result;
    }

    // Copy keys to output buffers
    memcpy(public_key, keypair.public_key, FALCON_PUBLIC_KEY_BYTES);
    memcpy(secret_key, keypair.secret_key, FALCON_SECRET_KEY_BYTES);

    return 0;
}

/**
 * Sign a message using Falcon
 */
int hydra_sign_message(
    const uint8_t* message,
    size_t message_len,
    const uint8_t* secret_key,
    uint8_t* signature,
    size_t* signature_len
) {
    if (!hydra_initialized || !message || message_len == 0 || 
        !secret_key || !signature || !signature_len) {
        return -1;
    }

    // Create a crypto key structure for Falcon
    crypto_key_t key;
    memset(&key, 0, sizeof(crypto_key_t));
    key.type = KEY_TYPE_FALCON;
    key.key_id = NULL;
    key.key_id_size = 0;
    memcpy(key.key_data.falcon.secret_key, secret_key, FALCON_SECRET_KEY_BYTES);

    // Sign the message
    return crypto_sign_message(signature, signature_len, message, message_len, &key);
}

/**
 * Verify a message signature using Falcon
 */
int hydra_verify_signature(
    const uint8_t* message,
    size_t message_len,
    const uint8_t* signature,
    size_t signature_len,
    const uint8_t* public_key
) {
    if (!hydra_initialized || !message || message_len == 0 || 
        !signature || signature_len == 0 || !public_key) {
        return -1;
    }

    // Create a crypto key structure for Falcon
    crypto_key_t key;
    memset(&key, 0, sizeof(crypto_key_t));
    key.type = KEY_TYPE_FALCON;
    key.key_id = NULL;
    key.key_id_size = 0;
    memcpy(key.key_data.falcon.public_key, public_key, FALCON_PUBLIC_KEY_BYTES);

    // Verify the signature
    return crypto_verify_signature(signature, signature_len, message, message_len, &key);
}

/**
 * Create a shared key using Kyber key encapsulation
 */
int hydra_establish_shared_key(
    const uint8_t* public_key,
    uint8_t* shared_secret,
    uint8_t* ciphertext
) {
    if (!hydra_initialized || !public_key || !shared_secret || !ciphertext) {
        return -1;
    }

    // Create a crypto key structure for Kyber
    crypto_key_t key;
    memset(&key, 0, sizeof(crypto_key_t));
    key.type = KEY_TYPE_KYBER;
    key.key_id = NULL;
    key.key_id_size = 0;
    memcpy(key.key_data.kyber.public_key, public_key, KYBER_PUBLIC_KEY_BYTES);

    // Establish shared key
    size_t shared_secret_len = KYBER_SHARED_SECRET_BYTES;
    size_t ciphertext_len = KYBER_CIPHERTEXT_BYTES;
    
    return crypto_establish_key(
        shared_secret, &shared_secret_len,
        ciphertext, &ciphertext_len,
        &key
    );
}

/**
 * Decrypt a shared key using Kyber key decapsulation
 */
int hydra_receive_shared_key(
    const uint8_t* secret_key,
    const uint8_t* ciphertext,
    uint8_t* shared_secret
) {
    if (!hydra_initialized || !secret_key || !ciphertext || !shared_secret) {
        return -1;
    }

    // Create a crypto key structure for Kyber
    crypto_key_t key;
    memset(&key, 0, sizeof(crypto_key_t));
    key.type = KEY_TYPE_KYBER;
    key.key_id = NULL;
    key.key_id_size = 0;
    memcpy(key.key_data.kyber.secret_key, secret_key, KYBER_SECRET_KEY_BYTES);

    // Receive shared key
    size_t shared_secret_len = KYBER_SHARED_SECRET_BYTES;
    
    return crypto_receive_key(
        shared_secret, &shared_secret_len,
        ciphertext, KYBER_CIPHERTEXT_BYTES,
        &key
    );
}

/**
 * Generate a zero-knowledge proof
 */
int hydra_generate_zkproof(
    const uint8_t* secret,
    size_t secret_len,
    const uint8_t* public_input,
    size_t public_len,
    uint8_t* proof_out,
    size_t* proof_len
) {
    if (!hydra_initialized || !secret || secret_len == 0 || 
        !public_input || !proof_out || !proof_len) {
        return -1;
    }

    // Generate the proof
    qzkp_proof_t* proof = qzkp_generate_proof(secret, secret_len, public_input, public_len);
    if (!proof) {
        return -2;
    }

    // Calculate the total size needed for serialization
    size_t total_size = sizeof(size_t) * 3 + proof->commit_size + proof->challenge_size + proof->response_size;
    
    // Check if the output buffer is big enough
    if (*proof_len < total_size) {
        qzkp_free_proof(proof);
        *proof_len = total_size;  // Tell the caller how much space is needed
        return -3;
    }

    // Serialize the proof
    size_t* size_ptr = (size_t*)proof_out;
    size_ptr[0] = proof->commit_size;
    size_ptr[1] = proof->challenge_size;
    size_ptr[2] = proof->response_size;
    
    uint8_t* data_ptr = proof_out + (3 * sizeof(size_t));
    memcpy(data_ptr, proof->commitment, proof->commit_size);
    data_ptr += proof->commit_size;
    
    memcpy(data_ptr, proof->challenge, proof->challenge_size);
    data_ptr += proof->challenge_size;
    
    memcpy(data_ptr, proof->response, proof->response_size);
    
    // Set the actual length
    *proof_len = total_size;
    
    // Free the proof
    qzkp_free_proof(proof);
    
    return 0;
}

/**
 * Verify a zero-knowledge proof
 */
int hydra_verify_zkproof(
    const uint8_t* proof_data,
    size_t proof_len,
    const uint8_t* public_input,
    size_t public_len
) {
    if (!hydra_initialized || !proof_data || proof_len < (3 * sizeof(size_t)) || 
        !public_input) {
        return -1;
    }

    // Deserialize the proof
    const size_t* size_ptr = (const size_t*)proof_data;
    size_t commit_size = size_ptr[0];
    size_t challenge_size = size_ptr[1];
    size_t response_size = size_ptr[2];
    
    // Validate sizes
    size_t expected_size = (3 * sizeof(size_t)) + commit_size + challenge_size + response_size;
    if (proof_len < expected_size) {
        return -2;
    }
    
    // Extract proof components
    const uint8_t* data_ptr = proof_data + (3 * sizeof(size_t));
    const uint8_t* commitment = data_ptr;
    data_ptr += commit_size;
    
    const uint8_t* challenge = data_ptr;
    data_ptr += challenge_size;
    
    const uint8_t* response = data_ptr;
    
    // Create a proof structure
    qzkp_proof_t proof;
    proof.commit_size = commit_size;
    proof.challenge_size = challenge_size;
    proof.response_size = response_size;
    
    // Allocate and copy memory for proof components
    proof.commitment = (uint8_t*)malloc(commit_size);
    if (!proof.commitment) {
        return -3;
    }
    memcpy(proof.commitment, commitment, commit_size);
    
    proof.challenge = (uint8_t*)malloc(challenge_size);
    if (!proof.challenge) {
        free(proof.commitment);
        return -3;
    }
    memcpy(proof.challenge, challenge, challenge_size);
    
    proof.response = (uint8_t*)malloc(response_size);
    if (!proof.response) {
        free(proof.challenge);
        free(proof.commitment);
        return -3;
    }
    memcpy(proof.response, response, response_size);
    
    // Create verification parameters
    qzkp_verify_params_t params = {
        .epsilon = 0.001,
        .sample_count = 100
    };
    
    // Verify the proof
    bool result = qzkp_verify_proof(&proof, public_input, public_len, &params);
    
    // Free allocated memory
    free(proof.response);
    free(proof.challenge);
    free(proof.commitment);
    
    return result ? 1 : 0;
}

/**
 * Create a logical entanglement of multiple data items
 */
int hydra_create_entanglement(
    const uint8_t** data_items,
    const size_t* data_lengths,
    size_t count,
    uint8_t* output
) {
    if (!hydra_initialized || !data_items || !data_lengths || count == 0 || !output) {
        return -1;
    }

    // Create nodes for each data item
    entanglement_node_t** nodes = (entanglement_node_t**)malloc(count * sizeof(entanglement_node_t*));
    if (!nodes) {
        return -2;
    }
    
    for (size_t i = 0; i < count; i++) {
        nodes[i] = le_create_node(data_items[i], data_lengths[i]);
        if (!nodes[i]) {
            // Clean up previously allocated nodes
            for (size_t j = 0; j < i; j++) {
                le_free_node(nodes[j]);
            }
            free(nodes);
            return -3;
        }
    }
    
    // Create dependencies between nodes
    for (size_t i = 1; i < count; i++) {
        if (le_add_dependency(nodes[i], nodes[i-1]) != 0) {
            // Clean up all nodes
            for (size_t j = 0; j < count; j++) {
                le_free_node(nodes[j]);
            }
            free(nodes);
            return -4;
        }
    }
    
    // Create graph
    entanglement_graph_t* graph = le_create_graph(nodes, count);
    if (!graph) {
        // Clean up all nodes
        for (size_t i = 0; i < count; i++) {
            le_free_node(nodes[i]);
        }
        free(nodes);
        return -5;
    }
    
    // Calculate root hash
    int result = le_calculate_root_hash(graph);
    if (result != 0) {
        le_free_graph(graph);
        // Note: le_free_graph doesn't free the nodes themselves
        for (size_t i = 0; i < count; i++) {
            le_free_node(nodes[i]);
        }
        free(nodes);
        return result;
    }
    
    // Copy root hash to output
    memcpy(output, graph->root_hash, graph->hash_size);
    
    // Clean up
    le_free_graph(graph);
    // Note: le_free_graph doesn't free the nodes themselves
    for (size_t i = 0; i < count; i++) {
        le_free_node(nodes[i]);
    }
    free(nodes);
    
    return 0;
}

/**
 * Verify if data items match an entanglement hash
 */
int hydra_verify_entanglement(
    const uint8_t** data_items,
    const size_t* data_lengths,
    size_t count,
    const uint8_t* entanglement_hash
) {
    if (!hydra_initialized || !data_items || !data_lengths || 
        count == 0 || !entanglement_hash) {
        return -1;
    }

    // Create a temporary buffer for our calculated hash
    uint8_t calculated_hash[32];
    
    // Calculate the entanglement hash
    int result = hydra_create_entanglement(data_items, data_lengths, count, calculated_hash);
    if (result != 0) {
        return result;
    }
    
    // Compare the calculated hash with the provided hash
    return (memcmp(calculated_hash, entanglement_hash, 32) == 0) ? 1 : 0;
}
