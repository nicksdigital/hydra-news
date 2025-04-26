#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include <stdbool.h>
#include <time.h>
#include <math.h>
#include "../c/src/postquantum/kyber.h"
#include "../c/src/postquantum/falcon.h"
#include "../c/src/postquantum/crypto_adapter.h"

// Test case structure
typedef struct {
    const char* name;
    bool (*test_func)(void);
} test_case_t;

// Global test statistics
int tests_run = 0;
int tests_passed = 0;

/**
 * Test Kyber key generation, encapsulation, and decapsulation
 */
bool test_kyber_key_exchange() {
    printf("Running test: Kyber Key Exchange\n");
    
    // Initialize Kyber
    int init_result = kyber_init();
    assert(init_result == 0);
    
    // Generate keypair
    kyber_keypair_t keypair;
    int keygen_result = kyber_keygen(&keypair);
    assert(keygen_result == 0);
    
    // Generate ciphertext and shared secret (sender side)
    uint8_t ciphertext[KYBER_CIPHERTEXT_BYTES];
    uint8_t shared_secret1[KYBER_SHARED_SECRET_BYTES];
    int encap_result = kyber_encapsulate(ciphertext, shared_secret1, keypair.public_key);
    assert(encap_result == 0);
    
    // Recover shared secret (receiver side)
    uint8_t shared_secret2[KYBER_SHARED_SECRET_BYTES];
    int decap_result = kyber_decapsulate(shared_secret2, ciphertext, keypair.secret_key);
    assert(decap_result == 0);
    
    // Verify shared secrets match
    bool secrets_match = (memcmp(shared_secret1, shared_secret2, KYBER_SHARED_SECRET_BYTES) == 0);
    assert(secrets_match);
    
    // Clean up
    kyber_cleanup();
    
    printf("Shared secrets match: %s\n", secrets_match ? "Yes" : "No");
    printf("Test result: %s\n", secrets_match ? "PASSED" : "FAILED");
    return secrets_match;
}

/**
 * Test Falcon signature generation and verification
 */
bool test_falcon_signatures() {
    printf("Running test: Falcon Signatures\n");
    
    // Initialize Falcon
    int init_result = falcon_init();
    assert(init_result == 0);
    printf("Falcon initialized successfully\n");
    
    // Generate keypair
    falcon_keypair_t keypair;
    int keygen_result = falcon_keygen(&keypair);
    assert(keygen_result == 0);
    printf("Falcon keypair generated successfully\n");
    
    // Message to sign
    const uint8_t message[] = "This is a test message that will be signed with Falcon";
    size_t message_len = strlen((const char*)message);
    
    // Sign the message
    uint8_t signature[FALCON_SIGNATURE_MAX_BYTES];
    size_t signature_len = FALCON_SIGNATURE_MAX_BYTES;
    int sign_result = falcon_sign(signature, &signature_len, message, message_len, keypair.secret_key);
    
    if (sign_result != 0) {
        printf("Signature generation failed with error code: %d\n", sign_result);
        assert(0); // Force test failure
    }
    
    assert(signature_len > 0 && signature_len <= FALCON_SIGNATURE_MAX_BYTES);
    printf("Signature generated successfully (length: %zu bytes)\n", signature_len);
    
    // Verify the signature
    int verify_result = falcon_verify(signature, signature_len, message, message_len, keypair.public_key);
    
    if (verify_result < 0) {
        printf("Signature verification failed with error code: %d\n", verify_result);
    } else if (verify_result == 0) {
        printf("Signature verification failed: invalid signature\n");
    } else {
        printf("Signature verification successful\n");
    }
    
    assert(verify_result == 1);
    
    // Verify with modified message (should fail)
    uint8_t modified_message[message_len];
    memcpy(modified_message, message, message_len);
    modified_message[message_len / 2] ^= 1;  // Flip a bit
    
    int verify_modified_result = falcon_verify(signature, signature_len, modified_message, message_len, keypair.public_key);
    
    if (verify_modified_result < 0) {
        printf("Modified message verification returned error code: %d\n", verify_modified_result);
    } else if (verify_modified_result == 0) {
        printf("Modified message correctly rejected\n");
    } else {
        printf("WARNING: Modified message incorrectly accepted!\n");
    }
    
    assert(verify_modified_result != 1); // Should either be 0 (invalid) or negative (error)
    
    // Clean up
    falcon_cleanup();
    printf("Modified message rejected: %s\n", (verify_modified_result == 0) ? "Yes" : "No");
    printf("Test result: %s\n", (verify_result == 1 && verify_modified_result == 0) ? "PASSED" : "FAILED");
    return (verify_result == 1 && verify_modified_result == 0);
}

/**
 * Test crypto adapter initialization and key generation
 */
bool test_crypto_adapter_init() {
    printf("Running test: Crypto Adapter Initialization\n");
    
    // Initialize adapter
    crypto_adapter_params_t params = {
        .use_pq_crypto = true,
        .use_hybrid = true,
        .key_storage_path = NULL
    };
    
    int init_result = crypto_adapter_init(&params);
    assert(init_result == 0);
    
    // Generate different types of keys
    crypto_key_t symmetric_key;
    int sym_result = crypto_generate_key(KEY_TYPE_SYMMETRIC, &symmetric_key, 3600);
    assert(sym_result == 0);
    
    crypto_key_t kyber_key;
    int kyber_result = crypto_generate_key(KEY_TYPE_KYBER, &kyber_key, 3600);
    assert(kyber_result == 0);
    
    crypto_key_t falcon_key;
    int falcon_result = crypto_generate_key(KEY_TYPE_FALCON, &falcon_key, 3600);
    assert(falcon_result == 0);
    
    // Verify keys were generated correctly
    assert(symmetric_key.key_data.symmetric.key != NULL);
    assert(symmetric_key.key_data.symmetric.key_size == 32);
    
    // Free keys
    crypto_free_key(&symmetric_key);
    crypto_free_key(&kyber_key);
    crypto_free_key(&falcon_key);
    
    // Clean up
    crypto_adapter_cleanup();
    
    bool success = (init_result == 0 && sym_result == 0 && kyber_result == 0 && falcon_result == 0);
    printf("Test result: %s\n", success ? "PASSED" : "FAILED");
    return success;
}

/**
 * Test signing and verification using crypto adapter
 */
bool test_crypto_adapter_signatures() {
    printf("Running test: Crypto Adapter Signatures\n");
    
    // Initialize adapter
    crypto_adapter_params_t params = {
        .use_pq_crypto = true,
        .use_hybrid = true,
        .key_storage_path = NULL
    };
    
    int init_result = crypto_adapter_init(&params);
    assert(init_result == 0);
    printf("Crypto adapter initialized successfully\n");
    
    // Generate Falcon key
    crypto_key_t falcon_key;
    int key_result = crypto_generate_key(KEY_TYPE_FALCON, &falcon_key, 0);
    assert(key_result == 0);
    printf("Falcon key generated successfully through crypto adapter\n");
    
    // Message to sign
    const uint8_t message[] = "This is a test message for the crypto adapter";
    size_t message_len = strlen((const char*)message);
    
    // Sign the message
    uint8_t signature[FALCON_SIGNATURE_MAX_BYTES];
    size_t signature_len = FALCON_SIGNATURE_MAX_BYTES;
    int sign_result = crypto_sign_message(signature, &signature_len, message, message_len, &falcon_key);
    
    if (sign_result != 0) {
        printf("Crypto adapter signature generation failed with error code: %d\n", sign_result);
        assert(0); // Force test failure
    } else {
        printf("Crypto adapter signature generated successfully (length: %zu bytes)\n", signature_len);
    }
    
    assert(signature_len > 0 && signature_len <= FALCON_SIGNATURE_MAX_BYTES);
    
    // Verify the signature
    int verify_result = crypto_verify_signature(signature, signature_len, message, message_len, &falcon_key);
    
    if (verify_result < 0) {
        printf("Crypto adapter signature verification failed with error code: %d\n", verify_result);
    } else if (verify_result == 0) {
        printf("Crypto adapter signature verification failed: invalid signature\n");
    } else {
        printf("Crypto adapter signature verification successful\n");
    }
    
    assert(verify_result == 1);
    
    // Verify with modified message (should fail)
    uint8_t modified_message[message_len];
    memcpy(modified_message, message, message_len);
    modified_message[message_len / 2] ^= 1;  // Flip a bit
    
    int verify_modified_result = crypto_verify_signature(signature, signature_len, modified_message, message_len, &falcon_key);
    
    if (verify_modified_result < 0) {
        printf("Modified message verification returned error code: %d\n", verify_modified_result);
    } else if (verify_modified_result == 0) {
        printf("Modified message correctly rejected by crypto adapter\n");
    } else {
        printf("WARNING: Modified message incorrectly accepted by crypto adapter!\n");
    }
    
    assert(verify_modified_result != 1); // Should either be 0 (invalid) or negative (error)
    
    // Free keys
    crypto_free_key(&falcon_key);
    
    // Clean up
    crypto_adapter_cleanup();
    printf("Crypto adapter resources cleaned up\n");
    
    bool success = (sign_result == 0 && verify_result == 1 && verify_modified_result != 1);
    printf("Test result: %s\n", success ? "PASSED" : "FAILED");
    return success;
}

/**
 * Test key exchange using crypto adapter
 */
bool test_crypto_adapter_key_exchange() {
    printf("Running test: Crypto Adapter Key Exchange\n");
    
    // Initialize adapter
    crypto_adapter_params_t params = {
        .use_pq_crypto = true,
        .use_hybrid = true,
        .key_storage_path = NULL
    };
    
    int init_result = crypto_adapter_init(&params);
    assert(init_result == 0);
    
    // Generate Kyber key
    crypto_key_t kyber_key;
    int key_result = crypto_generate_key(KEY_TYPE_KYBER, &kyber_key, 0);
    assert(key_result == 0);
    
    // Establish key (sender side)
    uint8_t shared_secret1[KYBER_SHARED_SECRET_BYTES];
    size_t shared_secret1_len = 0;
    uint8_t ciphertext[KYBER_CIPHERTEXT_BYTES];
    size_t ciphertext_len = 0;
    
    int encap_result = crypto_establish_key(shared_secret1, &shared_secret1_len, 
                                          ciphertext, &ciphertext_len, &kyber_key);
    assert(encap_result == 0);
    
    // Receive key (receiver side)
    uint8_t shared_secret2[KYBER_SHARED_SECRET_BYTES];
    size_t shared_secret2_len = 0;
    
    int decap_result = crypto_receive_key(shared_secret2, &shared_secret2_len, 
                                        ciphertext, ciphertext_len, &kyber_key);
    assert(decap_result == 0);
    
    // Verify shared secrets match
    bool secrets_match = (shared_secret1_len == shared_secret2_len && 
                         memcmp(shared_secret1, shared_secret2, shared_secret1_len) == 0);
    assert(secrets_match);
    
    // Free keys
    crypto_free_key(&kyber_key);
    
    // Clean up
    crypto_adapter_cleanup();
    
    printf("Shared secrets match: %s\n", secrets_match ? "Yes" : "No");
    printf("Test result: %s\n", secrets_match ? "PASSED" : "FAILED");
    return secrets_match;
}

/**
 * Test zero-knowledge proofs with post-quantum security
 */
bool test_crypto_adapter_zkproofs() {
    printf("Running test: Crypto Adapter Zero-Knowledge Proofs\n");
    
    // Initialize adapter
    crypto_adapter_params_t params = {
        .use_pq_crypto = true,
        .use_hybrid = true,
        .key_storage_path = NULL
    };
    
    int init_result = crypto_adapter_init(&params);
    assert(init_result == 0);
    printf("Crypto adapter initialized successfully\n");
    
    // Generate Falcon key
    crypto_key_t falcon_key;
    int key_result = crypto_generate_key(KEY_TYPE_FALCON, &falcon_key, 0);
    assert(key_result == 0);
    printf("Falcon key generated successfully\n");
    
    // Secret and public input
    const char* secret = "this_is_a_secret_that_should_remain_hidden";
    size_t secret_size = strlen(secret);
    const char* public_input = "public_input_for_verification";
    size_t public_input_size = strlen(public_input);
    printf("Test data prepared\n");
    
    // Generate zero-knowledge proof
    qzkp_proof_t* proof = NULL;
    int proof_result = crypto_generate_zkproof(&proof, secret, secret_size, 
                                             public_input, public_input_size, &falcon_key);
    
    printf("ZKP Proof generation result: %d\n", proof_result);
    
    // Make sure proof was created
    assert(proof_result == 0);
    assert(proof != NULL);
    printf("Proof structure validated\n");
    
    // Verification parameters
    qzkp_verify_params_t verify_params = {
        .epsilon = 0.001,
        .sample_count = 100
    };
    
    // Verify proof with correct data
    int verify_result = crypto_verify_zkproof(proof, public_input, public_input_size, 
                                            &falcon_key, &verify_params);
    printf("Verification with correct input: %s\n", verify_result == 1 ? "PASSED" : "FAILED");
    assert(verify_result == 1);
    
    // Create a modified input
    char modified_input[public_input_size + 1];
    strcpy(modified_input, public_input);
    modified_input[public_input_size / 2] ^= 1;  // Flip a bit
    
    // Verify with modified input (should fail)
    int verify_modified_result = crypto_verify_zkproof(proof, modified_input, public_input_size, 
                                                     &falcon_key, &verify_params);
    printf("Verification with modified input: %s\n", 
           verify_modified_result == 0 ? "CORRECTLY REJECTED" : "INCORRECTLY ACCEPTED");
    assert(verify_modified_result == 0);
    
    // Free resources
    if (proof) {
        qzkp_free_proof(proof);
    }
    
    crypto_free_key(&falcon_key);
    
    // Clean up
    crypto_adapter_cleanup();
    printf("Resources cleaned up\n");
    
    bool success = (proof_result == 0 && verify_result == 1 && verify_modified_result == 0);
    printf("Test result: %s\n", success ? "PASSED" : "FAILED");
    return success;
}

/**
 * Main test function
 */
int main() {
    printf("=== Hydra News Post-Quantum Cryptography Tests ===\n\n");
    
    // Define test cases
    test_case_t tests[] = {
        {"Kyber Key Exchange", test_kyber_key_exchange},
        {"Falcon Signatures", test_falcon_signatures},
        {"Crypto Adapter Initialization", test_crypto_adapter_init},
        {"Crypto Adapter Signatures", test_crypto_adapter_signatures},
        {"Crypto Adapter Key Exchange", test_crypto_adapter_key_exchange},
        {"Crypto Adapter Zero-Knowledge Proofs", test_crypto_adapter_zkproofs}
    };
    
    int test_count = sizeof(tests) / sizeof(tests[0]);
    
    // Run all tests
    for (int i = 0; i < test_count; i++) {
        printf("\n--- Test %d/%d: %s ---\n", i + 1, test_count, tests[i].name);
        tests_run++;
        if (tests[i].test_func()) {
            tests_passed++;
        }
    }
    
    // Print test summary
    printf("\n=== Test Summary ===\n");
    printf("Tests run: %d\n", tests_run);
    printf("Tests passed: %d\n", tests_passed);
    printf("Tests failed: %d\n", tests_run - tests_passed);
    printf("Success rate: %.2f%%\n", 100.0 * tests_passed / tests_run);
    
    return tests_passed == tests_run ? 0 : 1;
}
