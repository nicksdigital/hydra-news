#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <assert.h>
#include "../include/postquantum/crypto_adapter.h"
#include "../include/postquantum/kyber.h"
#include "../include/postquantum/falcon.h"
#include "../include/quantum_zkp.h"
#include "../include/logical_entanglement.h"

// Test parameters
#define NUM_TESTS 100
#define MAX_DATA_SIZE 1024
#define MAX_ITERATIONS 1000

// Test fixture for colored output
#define ANSI_COLOR_RED     "\x1b[31m"
#define ANSI_COLOR_GREEN   "\x1b[32m"
#define ANSI_COLOR_YELLOW  "\x1b[33m"
#define ANSI_COLOR_RESET   "\x1b[0m"

// Helper functions for tests
void generate_random_data(unsigned char *data, size_t size) {
    for (size_t i = 0; i < size; i++) {
        data[i] = (unsigned char)rand();
    }
}

void print_test_result(const char *test_name, int success) {
    if (success) {
        printf(ANSI_COLOR_GREEN "✓ %s" ANSI_COLOR_RESET "\n", test_name);
    } else {
        printf(ANSI_COLOR_RED "✗ %s" ANSI_COLOR_RESET "\n", test_name);
    }
}

// Test wrapper
int run_test(const char *test_name, int (*test_func)(void)) {
    printf("Running test: %s\n", test_name);
    int result = test_func();
    print_test_result(test_name, result);
    return result;
}

// Kyber tests
int test_kyber_key_generation() {
    unsigned char public_key[KYBER_PUBLIC_KEY_BYTES];
    unsigned char secret_key[KYBER_SECRET_KEY_BYTES];
    
    for (int i = 0; i < NUM_TESTS; i++) {
        if (kyber_keypair(public_key, secret_key) != 0) {
            printf("  Error in kyber_keypair() at iteration %d\n", i);
            return 0;
        }
    }
    
    return 1;
}

int test_kyber_encapsulation() {
    unsigned char public_key[KYBER_PUBLIC_KEY_BYTES];
    unsigned char secret_key[KYBER_SECRET_KEY_BYTES];
    unsigned char ciphertext[KYBER_CIPHERTEXT_BYTES];
    unsigned char shared_secret1[KYBER_SHARED_SECRET_BYTES];
    unsigned char shared_secret2[KYBER_SHARED_SECRET_BYTES];
    
    for (int i = 0; i < NUM_TESTS; i++) {
        // Generate a keypair
        if (kyber_keypair(public_key, secret_key) != 0) {
            printf("  Error in kyber_keypair() at iteration %d\n", i);
            return 0;
        }
        
        // Encapsulate to get a shared secret and a ciphertext
        if (kyber_encapsulate(ciphertext, shared_secret1, public_key) != 0) {
            printf("  Error in kyber_encapsulate() at iteration %d\n", i);
            return 0;
        }
        
        // Decapsulate the ciphertext to get the shared secret
        if (kyber_decapsulate(shared_secret2, ciphertext, secret_key) != 0) {
            printf("  Error in kyber_decapsulate() at iteration %d\n", i);
            return 0;
        }
        
        // Verify that the shared secrets match
        if (memcmp(shared_secret1, shared_secret2, KYBER_SHARED_SECRET_BYTES) != 0) {
            printf("  Shared secrets do not match at iteration %d\n", i);
            return 0;
        }
    }
    
    return 1;
}

// Falcon tests
int test_falcon_key_generation() {
    unsigned char public_key[FALCON_PUBLIC_KEY_BYTES];
    unsigned char secret_key[FALCON_SECRET_KEY_BYTES];
    
    for (int i = 0; i < NUM_TESTS; i++) {
        if (falcon_keygen(public_key, secret_key) != 0) {
            printf("  Error in falcon_keygen() at iteration %d\n", i);
            return 0;
        }
    }
    
    return 1;
}

int test_falcon_sign_verify() {
    unsigned char public_key[FALCON_PUBLIC_KEY_BYTES];
    unsigned char secret_key[FALCON_SECRET_KEY_BYTES];
    unsigned char message[MAX_DATA_SIZE];
    unsigned char signature[FALCON_SIGNATURE_BYTES];
    unsigned long long signature_len;
    
    for (int i = 0; i < NUM_TESTS; i++) {
        // Generate a keypair
        if (falcon_keygen(public_key, secret_key) != 0) {
            printf("  Error in falcon_keygen() at iteration %d\n", i);
            return 0;
        }
        
        // Generate a random message
        size_t message_len = rand() % MAX_DATA_SIZE + 1;
        generate_random_data(message, message_len);
        
        // Sign the message
        if (falcon_sign(signature, &signature_len, message, message_len, secret_key) != 0) {
            printf("  Error in falcon_sign() at iteration %d\n", i);
            return 0;
        }
        
        // Verify the signature
        if (falcon_verify(message, message_len, signature, signature_len, public_key) != 0) {
            printf("  Error in falcon_verify() at iteration %d\n", i);
            return 0;
        }
        
        // Tamper with the message and verify that verification fails
        message[0] ^= 0x01;
        if (falcon_verify(message, message_len, signature, signature_len, public_key) == 0) {
            printf("  Verification succeeded with tampered message at iteration %d\n", i);
            return 0;
        }
    }
    
    return 1;
}

// QZKP tests
int test_qzkp_proof_verification() {
    qzkp_public_params_t params;
    qzkp_proof_t proof;
    qzkp_witness_t witness;
    qzkp_statement_t statement;
    
    for (int i = 0; i < NUM_TESTS; i++) {
        // Initialize the parameters
        qzkp_init_params(&params);
        
        // Generate a random witness and statement
        qzkp_generate_witness(&witness);
        qzkp_derive_statement(&statement, &witness, &params);
        
        // Generate a proof
        if (qzkp_generate_proof(&proof, &witness, &statement, &params) != 0) {
            printf("  Error in qzkp_generate_proof() at iteration %d\n", i);
            return 0;
        }
        
        // Verify the proof
        if (qzkp_verify_proof(&proof, &statement, &params) != 0) {
            printf("  Error in qzkp_verify_proof() at iteration %d\n", i);
            return 0;
        }
        
        // Tamper with the statement and verify that verification fails
        statement.value[0] ^= 0x01;
        if (qzkp_verify_proof(&proof, &statement, &params) == 0) {
            printf("  Verification succeeded with tampered statement at iteration %d\n", i);
            return 0;
        }
    }
    
    return 1;
}

// Logical Entanglement tests
int test_logical_entanglement() {
    unsigned char data1[MAX_DATA_SIZE];
    unsigned char data2[MAX_DATA_SIZE];
    le_entanglement_t entanglement;
    
    for (int i = 0; i < NUM_TESTS; i++) {
        size_t data1_len = rand() % MAX_DATA_SIZE + 1;
        size_t data2_len = rand() % MAX_DATA_SIZE + 1;
        
        generate_random_data(data1, data1_len);
        generate_random_data(data2, data2_len);
        
        // Create entanglement between data1 and data2
        if (le_create_entanglement(&entanglement, data1, data1_len, data2, data2_len) != 0) {
            printf("  Error in le_create_entanglement() at iteration %d\n", i);
            return 0;
        }
        
        // Verify the entanglement
        if (le_verify_entanglement(&entanglement, data1, data1_len, data2, data2_len) != 0) {
            printf("  Error in le_verify_entanglement() at iteration %d\n", i);
            return 0;
        }
        
        // Tamper with data1 and verify that verification fails
        data1[0] ^= 0x01;
        if (le_verify_entanglement(&entanglement, data1, data1_len, data2, data2_len) == 0) {
            printf("  Verification succeeded with tampered data at iteration %d\n", i);
            return 0;
        }
    }
    
    return 1;
}

// Crypto Adapter tests
int test_crypto_adapter_hybrid_encryption() {
    unsigned char plaintext[MAX_DATA_SIZE];
    unsigned char ciphertext[MAX_DATA_SIZE + CRYPTO_ADAPTER_OVERHEAD];
    unsigned char decrypted[MAX_DATA_SIZE];
    unsigned long long ciphertext_len, decrypted_len;
    
    crypto_adapter_keypair_t keypair;
    
    for (int i = 0; i < NUM_TESTS; i++) {
        // Generate a keypair
        if (crypto_adapter_generate_keypair(&keypair) != 0) {
            printf("  Error in crypto_adapter_generate_keypair() at iteration %d\n", i);
            return 0;
        }
        
        // Generate a random plaintext
        size_t plaintext_len = rand() % MAX_DATA_SIZE + 1;
        generate_random_data(plaintext, plaintext_len);
        
        // Encrypt the plaintext
        if (crypto_adapter_encrypt(ciphertext, &ciphertext_len, plaintext, plaintext_len, &keypair.public_key) != 0) {
            printf("  Error in crypto_adapter_encrypt() at iteration %d\n", i);
            return 0;
        }
        
        // Decrypt the ciphertext
        if (crypto_adapter_decrypt(decrypted, &decrypted_len, ciphertext, ciphertext_len, &keypair.secret_key) != 0) {
            printf("  Error in crypto_adapter_decrypt() at iteration %d\n", i);
            return 0;
        }
        
        // Verify that the decrypted plaintext matches the original
        if (decrypted_len != plaintext_len || memcmp(plaintext, decrypted, plaintext_len) != 0) {
            printf("  Decrypted data does not match original at iteration %d\n", i);
            return 0;
        }
    }
    
    return 1;
}

int test_crypto_adapter_hybrid_signature() {
    unsigned char message[MAX_DATA_SIZE];
    unsigned char signature[CRYPTO_ADAPTER_MAX_SIGNATURE_SIZE];
    unsigned long long signature_len;
    
    crypto_adapter_keypair_t keypair;
    
    for (int i = 0; i < NUM_TESTS; i++) {
        // Generate a keypair
        if (crypto_adapter_generate_keypair(&keypair) != 0) {
            printf("  Error in crypto_adapter_generate_keypair() at iteration %d\n", i);
            return 0;
        }
        
        // Generate a random message
        size_t message_len = rand() % MAX_DATA_SIZE + 1;
        generate_random_data(message, message_len);
        
        // Sign the message
        if (crypto_adapter_sign(signature, &signature_len, message, message_len, &keypair.secret_key) != 0) {
            printf("  Error in crypto_adapter_sign() at iteration %d\n", i);
            return 0;
        }
        
        // Verify the signature
        if (crypto_adapter_verify(message, message_len, signature, signature_len, &keypair.public_key) != 0) {
            printf("  Error in crypto_adapter_verify() at iteration %d\n", i);
            return 0;
        }
        
        // Tamper with the message and verify that verification fails
        message[0] ^= 0x01;
        if (crypto_adapter_verify(message, message_len, signature, signature_len, &keypair.public_key) == 0) {
            printf("  Verification succeeded with tampered message at iteration %d\n", i);
            return 0;
        }
    }
    
    return 1;
}

// Integration tests
int test_secure_news_verification_flow() {
    // This test simulates the complete flow of news verification:
    // 1. Generate author credentials with QZKP
    // 2. Create a news article with logical entanglement
    // 3. Sign it with Falcon
    // 4. Encrypt sensitive parts with Kyber
    // 5. Verify the entire chain
    
    printf("Testing complete news verification flow...\n");
    
    // Create simulated news article
    unsigned char article_content[MAX_DATA_SIZE];
    size_t article_len = MAX_DATA_SIZE / 2;
    generate_random_data(article_content, article_len);
    
    // Create simulated metadata
    unsigned char metadata[MAX_DATA_SIZE / 4];
    size_t metadata_len = MAX_DATA_SIZE / 4;
    generate_random_data(metadata, metadata_len);
    
    // 1. Generate author credentials with QZKP
    qzkp_public_params_t params;
    qzkp_proof_t proof;
    qzkp_witness_t witness; // Author's private credentials
    qzkp_statement_t statement; // Public statement about the author
    
    qzkp_init_params(&params);
    qzkp_generate_witness(&witness);
    qzkp_derive_statement(&statement, &witness, &params);
    
    if (qzkp_generate_proof(&proof, &witness, &statement, &params) != 0) {
        printf("  Error in generating author credentials\n");
        return 0;
    }
    
    // 2. Create logical entanglement between content and metadata
    le_entanglement_t entanglement;
    if (le_create_entanglement(&entanglement, article_content, article_len, metadata, metadata_len) != 0) {
        printf("  Error in creating logical entanglement\n");
        return 0;
    }
    
    // 3. Sign the article with Falcon
    unsigned char falcon_public_key[FALCON_PUBLIC_KEY_BYTES];
    unsigned char falcon_secret_key[FALCON_SECRET_KEY_BYTES];
    unsigned char signature[FALCON_SIGNATURE_BYTES];
    unsigned long long signature_len;
    
    if (falcon_keygen(falcon_public_key, falcon_secret_key) != 0) {
        printf("  Error in generating author's signature key\n");
        return 0;
    }
    
    // Create a combined buffer with content + entanglement hash for signing
    unsigned char to_sign[MAX_DATA_SIZE * 2];
    memcpy(to_sign, article_content, article_len);
    memcpy(to_sign + article_len, entanglement.hash, sizeof(entanglement.hash));
    size_t to_sign_len = article_len + sizeof(entanglement.hash);
    
    if (falcon_sign(signature, &signature_len, to_sign, to_sign_len, falcon_secret_key) != 0) {
        printf("  Error in signing the article\n");
        return 0;
    }
    
    // 4. Encrypt sensitive parts with Kyber
    unsigned char kyber_public_key[KYBER_PUBLIC_KEY_BYTES];
    unsigned char kyber_secret_key[KYBER_SECRET_KEY_BYTES];
    unsigned char ciphertext[KYBER_CIPHERTEXT_BYTES];
    unsigned char shared_secret1[KYBER_SHARED_SECRET_BYTES];
    unsigned char shared_secret2[KYBER_SHARED_SECRET_BYTES];
    
    if (kyber_keypair(kyber_public_key, kyber_secret_key) != 0) {
        printf("  Error in generating encryption key\n");
        return 0;
    }
    
    if (kyber_encapsulate(ciphertext, shared_secret1, kyber_public_key) != 0) {
        printf("  Error in encrypting sensitive parts\n");
        return 0;
    }
    
    // 5. Verify the entire chain
    
    // Verify author credentials
    if (qzkp_verify_proof(&proof, &statement, &params) != 0) {
        printf("  Error in verifying author credentials\n");
        return 0;
    }
    
    // Verify signature
    if (falcon_verify(to_sign, to_sign_len, signature, signature_len, falcon_public_key) != 0) {
        printf("  Error in verifying article signature\n");
        return 0;
    }
    
    // Verify logical entanglement
    if (le_verify_entanglement(&entanglement, article_content, article_len, metadata, metadata_len) != 0) {
        printf("  Error in verifying logical entanglement\n");
        return 0;
    }
    
    // Decrypt sensitive parts
    if (kyber_decapsulate(shared_secret2, ciphertext, kyber_secret_key) != 0) {
        printf("  Error in decrypting sensitive parts\n");
        return 0;
    }
    
    if (memcmp(shared_secret1, shared_secret2, KYBER_SHARED_SECRET_BYTES) != 0) {
        printf("  Error in key agreement for sensitive parts\n");
        return 0;
    }
    
    printf("  Complete news verification flow succeeded\n");
    return 1;
}

// Performance tests
int test_key_generation_performance() {
    time_t start, end;
    double seconds;
    
    // Test Kyber key generation performance
    start = time(NULL);
    unsigned char kyber_public_key[KYBER_PUBLIC_KEY_BYTES];
    unsigned char kyber_secret_key[KYBER_SECRET_KEY_BYTES];
    
    for (int i = 0; i < MAX_ITERATIONS; i++) {
        kyber_keypair(kyber_public_key, kyber_secret_key);
    }
    
    end = time(NULL);
    seconds = difftime(end, start);
    printf("  Kyber key generation: %d iterations in %.2f seconds (%.2f ops/s)\n", 
           MAX_ITERATIONS, seconds, MAX_ITERATIONS / seconds);
    
    // Test Falcon key generation performance
    start = time(NULL);
    unsigned char falcon_public_key[FALCON_PUBLIC_KEY_BYTES];
    unsigned char falcon_secret_key[FALCON_SECRET_KEY_BYTES];
    
    for (int i = 0; i < MAX_ITERATIONS / 10; i++) { // Falcon is slower, so do fewer iterations
        falcon_keygen(falcon_public_key, falcon_secret_key);
    }
    
    end = time(NULL);
    seconds = difftime(end, start);
    printf("  Falcon key generation: %d iterations in %.2f seconds (%.2f ops/s)\n", 
           MAX_ITERATIONS / 10, seconds, (MAX_ITERATIONS / 10) / seconds);
    
    return 1;
}

int test_crypto_operations_performance() {
    time_t start, end;
    double seconds;
    
    // Prepare test data
    unsigned char data[MAX_DATA_SIZE];
    generate_random_data(data, MAX_DATA_SIZE);
    
    // Test Kyber encryption/decryption performance
    unsigned char kyber_public_key[KYBER_PUBLIC_KEY_BYTES];
    unsigned char kyber_secret_key[KYBER_SECRET_KEY_BYTES];
    unsigned char ciphertext[KYBER_CIPHERTEXT_BYTES];
    unsigned char shared_secret[KYBER_SHARED_SECRET_BYTES];
    
    kyber_keypair(kyber_public_key, kyber_secret_key);
    
    start = time(NULL);
    for (int i = 0; i < MAX_ITERATIONS; i++) {
        kyber_encapsulate(ciphertext, shared_secret, kyber_public_key);
    }
    end = time(NULL);
    seconds = difftime(end, start);
    printf("  Kyber encapsulation: %d iterations in %.2f seconds (%.2f ops/s)\n", 
           MAX_ITERATIONS, seconds, MAX_ITERATIONS / seconds);
    
    start = time(NULL);
    for (int i = 0; i < MAX_ITERATIONS; i++) {
        kyber_decapsulate(shared_secret, ciphertext, kyber_secret_key);
    }
    end = time(NULL);
    seconds = difftime(end, start);
    printf("  Kyber decapsulation: %d iterations in %.2f seconds (%.2f ops/s)\n", 
           MAX_ITERATIONS, seconds, MAX_ITERATIONS / seconds);
    
    // Test Falcon sign/verify performance
    unsigned char falcon_public_key[FALCON_PUBLIC_KEY_BYTES];
    unsigned char falcon_secret_key[FALCON_SECRET_KEY_BYTES];
    unsigned char signature[FALCON_SIGNATURE_BYTES];
    unsigned long long signature_len;
    
    falcon_keygen(falcon_public_key, falcon_secret_key);
    
    start = time(NULL);
    for (int i = 0; i < MAX_ITERATIONS / 10; i++) { // Falcon is slower, so do fewer iterations
        falcon_sign(signature, &signature_len, data, MAX_DATA_SIZE, falcon_secret_key);
    }
    end = time(NULL);
    seconds = difftime(end, start);
    printf("  Falcon signing: %d iterations in %.2f seconds (%.2f ops/s)\n", 
           MAX_ITERATIONS / 10, seconds, (MAX_ITERATIONS / 10) / seconds);
    
    start = time(NULL);
    for (int i = 0; i < MAX_ITERATIONS / 5; i++) { // Verification is faster than signing
        falcon_verify(data, MAX_DATA_SIZE, signature, signature_len, falcon_public_key);
    }
    end = time(NULL);
    seconds = difftime(end, start);
    printf("  Falcon verification: %d iterations in %.2f seconds (%.2f ops/s)\n", 
           MAX_ITERATIONS / 5, seconds, (MAX_ITERATIONS / 5) / seconds);
    
    return 1;
}

int main() {
    // Initialize random number generator
    srand(time(NULL));
    
    printf("Running Hydra News Cryptographic Tests\n");
    printf("======================================\n\n");
    
    int success_count = 0;
    int total_tests = 0;
    
    // Run Kyber tests
    printf("\nTesting CRYSTALS-Kyber (Post-Quantum KEM):\n");
    printf("------------------------------------------\n");
    success_count += run_test("Kyber key generation", test_kyber_key_generation); total_tests++;
    success_count += run_test("Kyber encapsulation/decapsulation", test_kyber_encapsulation); total_tests++;
    
    // Run Falcon tests
    printf("\nTesting Falcon (Post-Quantum Signature):\n");
    printf("----------------------------------------\n");
    success_count += run_test("Falcon key generation", test_falcon_key_generation); total_tests++;
    success_count += run_test("Falcon sign/verify", test_falcon_sign_verify); total_tests++;
    
    // Run QZKP tests
    printf("\nTesting Quantum Zero-Knowledge Proofs:\n");
    printf("-------------------------------------\n");
    success_count += run_test("QZKP proof verification", test_qzkp_proof_verification); total_tests++;
    
    // Run Logical Entanglement tests
    printf("\nTesting Logical Entanglement:\n");
    printf("----------------------------\n");
    success_count += run_test("Logical entanglement creation/verification", test_logical_entanglement); total_tests++;
    
    // Run Crypto Adapter tests
    printf("\nTesting Crypto Adapter:\n");
    printf("----------------------\n");
    success_count += run_test("Hybrid encryption/decryption", test_crypto_adapter_hybrid_encryption); total_tests++;
    success_count += run_test("Hybrid signature/verification", test_crypto_adapter_hybrid_signature); total_tests++;
    
    // Run Integration tests
    printf("\nTesting Integration:\n");
    printf("------------------\n");
    success_count += run_test("Secure news verification flow", test_secure_news_verification_flow); total_tests++;
    
    // Run Performance tests
    printf("\nPerformance Tests:\n");
    printf("----------------\n");
    success_count += run_test("Key generation performance", test_key_generation_performance); total_tests++;
    success_count += run_test("Crypto operations performance", test_crypto_operations_performance); total_tests++;
    
    // Print summary
    printf("\nTest Summary:\n");
    printf("------------\n");
    printf("Passed: %d/%d (%.1f%%)\n", success_count, total_tests, (float)success_count / total_tests * 100);
    
    if (success_count == total_tests) {
        printf("\n" ANSI_COLOR_GREEN "All tests passed! The cryptographic components are working correctly." ANSI_COLOR_RESET "\n");
        return 0;
    } else {
        printf("\n" ANSI_COLOR_RED "Some tests failed. Please review the output above." ANSI_COLOR_RESET "\n");
        return 1;
    }
}
