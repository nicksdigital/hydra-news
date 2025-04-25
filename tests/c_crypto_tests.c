#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include <stdbool.h>
#include <time.h>
#include <math.h>
#include "../c/src/quantum_zkp.h"

// Test case structure
typedef struct {
    const char* name;
    bool (*test_func)(void);
} test_case_t;

// Global test statistics
int tests_run = 0;
int tests_passed = 0;

/*
 * Test initialization and cleanup of the Quantum-ZKP system
 */
bool test_qzkp_init_cleanup() {
    printf("Running test: QZKP Init/Cleanup\n");
    
    // Initialize the QZKP system
    int init_result = qzkp_init();
    bool success = (init_result == 0);
    
    // Verify system is initialized
    assert(success);
    
    // Cleanup
    qzkp_cleanup();
    
    printf("Test result: %s\n", success ? "PASSED" : "FAILED");
    return success;
}

/*
 * Test generation of a zero-knowledge proof
 */
bool test_qzkp_proof_generation() {
    printf("Running test: QZKP Proof Generation\n");
    
    // Initialize the QZKP system
    int init_result = qzkp_init();
    assert(init_result == 0);
    
    // Create a secret
    const char* secret = "s3cret_value_that_should_remain_hidden";
    size_t secret_size = strlen(secret);
    
    // Create entropy
    const char* entropy = "additional_random_data";
    size_t entropy_size = strlen(entropy);
    
    // Generate proof
    qzkp_proof_t* proof = qzkp_generate_proof(
        secret, secret_size,
        entropy, entropy_size
    );
    
    // Verify proof was created successfully
    bool success = (proof != NULL);
    assert(success);
    
    // Verify proof properties
    assert(proof->commitment != NULL);
    assert(proof->commit_size > 0);
    assert(proof->challenge != NULL);
    assert(proof->challenge_size > 0);
    assert(proof->response != NULL);
    assert(proof->response_size > 0);
    
    // Free resources
    qzkp_free_proof(proof);
    qzkp_cleanup();
    
    printf("Test result: %s\n", success ? "PASSED" : "FAILED");
    return success;
}

/*
 * Test verification of a zero-knowledge proof
 */
bool test_qzkp_proof_verification() {
    printf("Running test: QZKP Proof Verification\n");
    
    // Initialize the QZKP system
    int init_result = qzkp_init();
    assert(init_result == 0);
    
    // Create a secret
    const char* secret = "s3cret_value_that_should_remain_hidden";
    size_t secret_size = strlen(secret);
    
    // Create entropy
    const char* entropy = "additional_random_data";
    size_t entropy_size = strlen(entropy);
    
    // Generate proof
    qzkp_proof_t* proof = qzkp_generate_proof(
        secret, secret_size,
        entropy, entropy_size
    );
    
    assert(proof != NULL);
    
    // Create public input for verification
    const char* public_input = "public_info_for_verification";
    size_t public_input_size = strlen(public_input);
    
    // Create verification parameters
    qzkp_verify_params_t verify_params = {
        .epsilon = 0.001,
        .sample_count = 100
    };
    
    // Verify the proof
    bool proof_valid = qzkp_verify_proof(
        proof,
        public_input, public_input_size,
        &verify_params
    );
    
    // Free resources
    qzkp_free_proof(proof);
    qzkp_cleanup();
    
    printf("Test result: %s\n", proof_valid ? "PASSED" : "FAILED");
    return proof_valid;
}

/*
 * Test creation of a superposition state
 */
bool test_superposition_creation() {
    printf("Running test: Superposition Creation\n");
    
    // Initialize the QZKP system
    int init_result = qzkp_init();
    assert(init_result == 0);
    
    // Create test states
    const int state_count = 3;
    const int state_size = sizeof(int);
    void* states[state_count];
    double amplitudes[state_count];
    
    // Initialize states and amplitudes
    for (int i = 0; i < state_count; i++) {
        states[i] = malloc(state_size);
        *((int*)states[i]) = i + 1;
        amplitudes[i] = 1.0 / sqrt(state_count);
    }
    
    // Create superposition
    qzkp_superposition_t* superposition = qzkp_create_superposition(
        states, amplitudes, state_count, state_size
    );
    
    // Verify superposition was created
    bool success = (superposition != NULL);
    assert(success);
    
    // Verify state count and size
    assert(superposition->state_count == state_count);
    assert(superposition->state_size == state_size);
    
    // Free resources
    for (int i = 0; i < state_count; i++) {
        free(states[i]);
    }
    qzkp_free_superposition(superposition);
    qzkp_cleanup();
    
    printf("Test result: %s\n", success ? "PASSED" : "FAILED");
    return success;
}

/*
 * Test logical entanglement
 */
bool test_logical_entanglement() {
    printf("Running test: Logical Entanglement\n");
    
    // Initialize the QZKP system
    int init_result = qzkp_init();
    assert(init_result == 0);
    
    // Create test states
    const int state_count = 3;
    const int state_size = 16;
    void* states[state_count];
    
    // Initialize states
    for (int i = 0; i < state_count; i++) {
        states[i] = malloc(state_size);
        // Fill with different patterns
        memset(states[i], 'A' + i, state_size);
    }
    
    // Apply entanglement
    uint8_t* entanglement_hash = qzkp_apply_entanglement(
        states, state_count, state_size
    );
    
    // Verify hash was created
    bool success = (entanglement_hash != NULL);
    assert(success);
    
    // Modify one state
    ((char*)states[1])[5] = 'X';
    
    // Apply entanglement again
    uint8_t* modified_hash = qzkp_apply_entanglement(
        states, state_count, state_size
    );
    
    assert(modified_hash != NULL);
    
    // Verify the hashes are different (tamper detection)
    bool hashes_different = (memcmp(
        entanglement_hash, modified_hash, 32 // SHA-256 length
    ) != 0);
    assert(hashes_different);
    
    // Free resources
    for (int i = 0; i < state_count; i++) {
        free(states[i]);
    }
    free(entanglement_hash);
    free(modified_hash);
    qzkp_cleanup();
    
    printf("Test result: %s\n", (success && hashes_different) ? "PASSED" : "FAILED");
    return success && hashes_different;
}

/*
 * Test probabilistic encoding
 */
bool test_probabilistic_encoding() {
    printf("Running test: Probabilistic Encoding\n");
    
    // Initialize the QZKP system
    int init_result = qzkp_init();
    assert(init_result == 0);
    
    // Create test data
    const char* data = "sensitive_data_to_be_encoded";
    size_t data_size = strlen(data);
    size_t samples = 1000;
    
    // Generate encoding
    uint8_t* encoded = qzkp_probabilistic_encode(
        data, data_size, samples
    );
    
    // Verify encoding was created
    bool success = (encoded != NULL);
    assert(success);
    
    // Generate second encoding
    uint8_t* encoded2 = qzkp_probabilistic_encode(
        data, data_size, samples
    );
    
    assert(encoded2 != NULL);
    
    // Verify the two encodings are different (probabilistic nature)
    size_t encoded_size = (samples + 7) / 8; // Size in bytes
    bool encodings_different = (memcmp(encoded, encoded2, encoded_size) != 0);
    
    // Print difference status
    printf("Encodings differ: %s\n", encodings_different ? "Yes" : "No");
    
    // Free resources
    free(encoded);
    free(encoded2);
    qzkp_cleanup();
    
    // Note: We don't assert encodings_different because it's probabilistic
    // and could theoretically be the same by chance
    
    printf("Test result: %s\n", success ? "PASSED" : "FAILED");
    return success;
}

/*
 * Main test function
 */
int main() {
    printf("=== Hydra News Cryptographic Tests ===\n\n");
    
    // Define test cases
    test_case_t tests[] = {
        {"QZKP Init/Cleanup", test_qzkp_init_cleanup},
        {"QZKP Proof Generation", test_qzkp_proof_generation},
        {"QZKP Proof Verification", test_qzkp_proof_verification},
        {"Superposition Creation", test_superposition_creation},
        {"Logical Entanglement", test_logical_entanglement},
        {"Probabilistic Encoding", test_probabilistic_encoding}
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
