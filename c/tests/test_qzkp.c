#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../include/quantum_zkp.h"

int main() {
    printf("Testing Quantum Zero-Knowledge Proof Implementation\n");
    
    // Initialize the QZKP system
    if (qzkp_init() != 0) {
        printf("Failed to initialize QZKP system\n");
        return 1;
    }
    
    printf("QZKP system initialized successfully\n");
    
    // Test data
    const char *secret = "This is a secret value that should be protected";
    const char *entropy = "Additional entropy for proof generation";
    
    // Generate a proof
    qzkp_proof_t *proof = qzkp_generate_proof(
        secret, strlen(secret),
        entropy, strlen(entropy)
    );
    
    if (proof == NULL) {
        printf("Failed to generate proof\n");
        qzkp_cleanup();
        return 1;
    }
    
    printf("Proof generated successfully\n");
    printf("Commitment size: %zu bytes\n", proof->commit_size);
    printf("Challenge size: %zu bytes\n", proof->challenge_size);
    printf("Response size: %zu bytes\n", proof->response_size);
    
    // Public input for verification
    const char *public_input = "Public information related to the proof";
    
    // Verification parameters
    qzkp_verify_params_t params = {
        .epsilon = 0.01,      // 1% error margin
        .sample_count = 100   // 100 verification samples
    };
    
    // Verify the proof
    if (qzkp_verify_proof(
            proof,
            public_input, strlen(public_input),
            &params
        )) {
        printf("Proof verification successful\n");
    } else {
        printf("Proof verification failed\n");
    }
    
    // Clean up
    qzkp_free_proof(proof);
    qzkp_cleanup();
    
    printf("QZKP test completed\n");
    return 0;
}
