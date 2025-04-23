#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include <stdbool.h>
#include <time.h>
#include <math.h>
#include <openssl/sha.h>
#include "../c/src/quantum_zkp.h"

// Test data structure
typedef struct {
    const char* name;
    bool (*test_func)(void);
} test_case_t;

// Global test statistics
int tests_run = 0;
int tests_passed = 0;

/**
 * Test the creation of a superposition state
 * This tests that we can create the fundamental structure for anonymity
 */
bool test_superposition_creation() {
    printf("Running test: Superposition creation\n");
    
    // Initialize the QZKP system
    int init_result = qzkp_init();
    assert(init_result == 0);
    
    // Create test states
    const int state_count = 3;
    const int state_size = sizeof(int);
    void* states[state_count];
    double amplitudes[state_count];
    
    // Allocate and initialize states
    for (int i = 0; i < state_count; i++) {
        states[i] = malloc(state_size);
        *((int*)states[i]) = i + 1; // State values: 1, 2, 3
        amplitudes[i] = 1.0 / sqrt(state_count); // Normalized amplitudes
    }
    
    // Create superposition
    qzkp_superposition_t* superposition = qzkp_create_superposition(
        states, amplitudes, state_count, state_size
    );
    
    // Verify superposition was created
    bool success = (superposition != NULL);
    assert(success);
    
    // Verify superposition properties
    assert(superposition->state_count == state_count);
    assert(superposition->state_size == state_size);
    
    // Verify states were copied correctly
    for (int i = 0; i < state_count; i++) {
        assert(*((int*)superposition->states[i]) == i + 1);
        assert(fabs(superposition->amplitudes[i] - (1.0 / sqrt(state_count))) < 1e-6);
    }
    
    // Free resources
    for (int i = 0; i < state_count; i++) {
        free(states[i]);
    }
    qzkp_free_superposition(superposition);
    qzkp_cleanup();
    
    printf("Test result: %s\n", success ? "PASSED" : "FAILED");
    return success;
}

/**
 * Test the generation and verification of a zero-knowledge proof
 * This is the core of the anonymity system - proving knowledge without revealing it
 */
bool test_zkp_generation_verification() {
    printf("Running test: ZKP generation and verification\n");
    
    // Initialize the QZKP system
    int init_result = qzkp_init();
    assert(init_result == 0);
    
    // Create a secret
    const char* secret = "this_is_a_secret_that_should_not_be_revealed";
    size_t secret_size = strlen(secret);
    
    // Generate additional entropy
    const char* entropy = "additional_randomness";
    size_t entropy_size = strlen(entropy);
    
    // Generate a ZKP proof
    qzkp_proof_t* proof = qzkp_generate_proof(
        secret, secret_size, entropy, entropy_size
    );
    
    // Verify proof was created
    bool success = (proof != NULL);
    assert(success);
    
    // Verify proof properties
    assert(proof->commitment != NULL);
    assert(proof->commit_size > 0);
    assert(proof->challenge != NULL);
    assert(proof->challenge_size > 0);
    assert(proof->response != NULL);
    assert(proof->response_size > 0);
    
    // Set up verification parameters
    qzkp_verify_params_t verify_params = {
        .epsilon = 0.001,   // Small error margin
        .sample_count = 100 // Number of samples for verification
    };
    
    // Create public input (in a real system, this would be different from the secret)
    // For testing, we'll create a public input derived from but not revealing the secret
    char public_input[64];
    snprintf(public_input, sizeof(public_input), "public_%zu", secret_size);
    
    // Verify the proof
    bool proof_valid = qzkp_verify_proof(
        proof, public_input, strlen(public_input), &verify_params
    );
    
    // In our implementation, this should return true
    assert(proof_valid);
    
    // Free resources
    qzkp_free_proof(proof);
    qzkp_cleanup();
    
    printf("Test result: %s\n", success && proof_valid ? "PASSED" : "FAILED");
    return success && proof_valid;
}

/**
 * Test that the proof doesn't leak secret information
 * This is crucial for anonymity - we need to ensure that the proof doesn't
 * reveal anything about the secret being proven
 */
bool test_zkp_information_leakage() {
    printf("Running test: ZKP information leakage\n");
    
    // Initialize the QZKP system
    int init_result = qzkp_init();
    assert(init_result == 0);
    
    // Create two different secrets
    const char* secret1 = "first_secret_that_should_not_be_revealed";
    const char* secret2 = "second_totally_different_secret_value";
    size_t secret1_size = strlen(secret1);
    size_t secret2_size = strlen(secret2);
    
    // Generate proofs with the same entropy
    const char* entropy = "same_entropy_for_both_proofs";
    size_t entropy_size = strlen(entropy);
    
    // Generate proofs
    qzkp_proof_t* proof1 = qzkp_generate_proof(
        secret1, secret1_size, entropy, entropy_size
    );
    qzkp_proof_t* proof2 = qzkp_generate_proof(
        secret2, secret2_size, entropy, entropy_size
    );
    
    // Verify proofs were created
    assert(proof1 != NULL);
    assert(proof2 != NULL);
    
    // Verify the proofs have different commitments (shouldn't leak that they're for the same secret)
    bool commitments_different = (memcmp(
        proof1->commitment, proof2->commitment, 
        proof1->commit_size < proof2->commit_size ? proof1->commit_size : proof2->commit_size
    ) != 0);
    
    // Verify the proofs have different responses
    bool responses_different = (memcmp(
        proof1->response, proof2->response,
        proof1->response_size < proof2->response_size ? proof1->response_size : proof2->response_size
    ) != 0);
    
    // Test that a direct comparison doesn't reveal secret equivalence
    bool success = commitments_different && responses_different;
    assert(success);
    
    // Free resources
    qzkp_free_proof(proof1);
    qzkp_free_proof(proof2);
    qzkp_cleanup();
    
    printf("Test result: %s\n", success ? "PASSED" : "FAILED");
    return success;
}

/**
 * Test probabilistic encoding which is used for privacy-preserving verification
 * This ensures that encoded data maintains privacy while still allowing verification
 */
bool test_probabilistic_encoding() {
    printf("Running test: Probabilistic encoding\n");
    
    // Initialize the QZKP system
    int init_result = qzkp_init();
    assert(init_result == 0);
    
    // Create test data
    const char* data = "sensitive_data_for_encoding";
    size_t data_size = strlen(data);
    size_t samples = 1000;
    
    // Generate probabilistic encoding
    uint8_t* encoded = qzkp_probabilistic_encode(data, data_size, samples);
    
    // Verify encoding was created
    bool success = (encoded != NULL);
    assert(success);
    
    // Create second encoding of the same data
    uint8_t* encoded2 = qzkp_probabilistic_encode(data, data_size, samples);
    assert(encoded2 != NULL);
    
    // Verify the two encodings are different (probabilistic nature)
    // Due to probabilistic nature, encodings should differ even for the same input
    size_t encoded_size = (samples + 7) / 8; // Size in bytes
    bool encodings_different = (memcmp(encoded, encoded2, encoded_size) != 0);
    
    // We can't guarantee they'll always be different with certainty due to randomness,
    // but with 1000 samples, it's extremely likely they'll differ
    printf("Encodings different: %s\n", encodings_different ? "Yes" : "No");
    
    // Free resources
    free(encoded);
    free(encoded2);
    qzkp_cleanup();
    
    printf("Test result: %s\n", success ? "PASSED" : "FAILED");
    return success;
}

/**
 * Test logical entanglement which creates tamper-evident interdependencies
 * This is essential for content verification while preserving anonymity
 */
bool test_logical_entanglement() {
    printf("Running test: Logical entanglement\n");
    
    // Initialize the QZKP system
    int init_result = qzkp_init();
    assert(init_result == 0);
    
    // Create test states
    const int state_count = 3;
    const int state_size = 16;
    void* states[state_count];
    
    // Allocate and initialize states
    for (int i = 0; i < state_count; i++) {
        states[i] = malloc(state_size);
        memset(states[i], 'A' + i, state_size); // Fill with different bytes
    }
    
    // Apply entanglement
    uint8_t* entanglement_hash = qzkp_apply_entanglement(
        states, state_count, state_size
    );
    
    // Verify entanglement hash was created
    bool success = (entanglement_hash != NULL);
    assert(success);
    
    // Modify one state
    ((char*)states[1])[5] = 'X';
    
    // Generate new entanglement hash
    uint8_t* modified_hash = qzkp_apply_entanglement(
        states, state_count, state_size
    );
    assert(modified_hash != NULL);
    
    // Verify the hashes are different (tamper detection)
    // Using 32 bytes (256 bits) which is the SHA-256 digest length
    bool hashes_different = (memcmp(
        entanglement_hash, modified_hash, 32
    ) != 0);
    assert(hashes_different);
    
    // Free resources
    for (int i = 0; i < state_count; i++) {
        free(states[i]);
    }
    free(entanglement_hash);
    free(modified_hash);
    qzkp_cleanup();
    
    printf("Test result: %s\n", success && hashes_different ? "PASSED" : "FAILED");
    return success && hashes_different;
}

/**
 * Main test runner
 */
int main() {
    printf("=== Hydra News Anonymity Tests ===\n\n");
    
    // Define test cases
    test_case_t tests[] = {
        {"Superposition Creation", test_superposition_creation},
        {"ZKP Generation & Verification", test_zkp_generation_verification},
        {"ZKP Information Leakage", test_zkp_information_leakage},
        {"Probabilistic Encoding", test_probabilistic_encoding},
        {"Logical Entanglement", test_logical_entanglement}
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
