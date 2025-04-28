#include "crypto_test_part3.c"

// Main function to run end-to-end cryptographic test
int main() {
    // Initialize all cryptographic components
    printf("Initializing cryptographic components...\n");
    
    if (qzkp_init() != 0) {
        fprintf(stderr, "Failed to initialize QZKP system\n");
        return 1;
    }
    
    if (le_init() != 0) {
        fprintf(stderr, "Failed to initialize logical entanglement system\n");
        qzkp_cleanup();
        return 1;
    }
    
    printf("Cryptographic components initialized successfully\n\n");
    
    // 1. Create a news source (journalist or whistleblower)
    printf("Creating and authenticating news source...\n");
    news_source_t* source = create_news_source(
        "journalist123",
        "Jane Smith",
        "Global News Network",
        40.7128,  // Latitude: New York City
        -74.0060, // Longitude: New York City
        "North America"
    );
    
    if (!source) {
        fprintf(stderr, "Failed to create news source\n");
        le_cleanup();
        qzkp_cleanup();
        return 1;
    }
    
    // 2. Generate zero-knowledge proofs for source
    if (generate_source_identity_proof(source) != 0) {
        fprintf(stderr, "Failed to generate identity proof for source\n");
        free_news_source(source);
        le_cleanup();
        qzkp_cleanup();
        return 1;
    }
    
    if (generate_source_location_proof(source) != 0) {
        fprintf(stderr, "Failed to generate location proof for source\n");
        free_news_source(source);
        le_cleanup();
        qzkp_cleanup();
        return 1;
    }
    
    printf("Source created and proofs generated successfully\n");
    
    // 3. Verify source identity and location without revealing private information
    if (verify_source_identity(source)) {
        printf("Source identity verified successfully\n");
    } else {
        fprintf(stderr, "Source identity verification failed\n");
        free_news_source(source);
        le_cleanup();
        qzkp_cleanup();
        return 1;
    }
    
    if (verify_source_location(source)) {
        printf("Source location verified successfully without revealing exact coordinates\n");
    } else {
        fprintf(stderr, "Source location verification failed\n");
        free_news_source(source);
        le_cleanup();
        qzkp_cleanup();
        return 1;
    }
    
    printf("\n");
    
    // 4. Create a news article
    printf("Creating news article with logical entanglement...\n");
    news_article_t* article = create_news_article(
        "Major Political Development in International Relations",
        "This is a breaking story about significant diplomatic negotiations between "
        "two major world powers that could reshape international relations. Multiple "
        "sources confirm that secret talks have been ongoing for months.",
        "Global News Network",
        "Jane Smith",
        "New York, USA"
    );
    
    if (!article) {
        fprintf(stderr, "Failed to create news article\n");
        free_news_source(source);
        le_cleanup();
        qzkp_cleanup();
        return 1;
    }
    
    // 5. Create logical entanglement for the article content
    if (create_article_entanglement(article) != 0) {
        fprintf(stderr, "Failed to create entanglement for article\n");
        free_news_article(article);
        free_news_source(source);
        le_cleanup();
        qzkp_cleanup();
        return 1;
    }
    
    printf("Article created with logical entanglement successfully\n");
    
    // 6. Sign the article with source's key
    if (sign_article(article, source) != 0) {
        fprintf(stderr, "Failed to sign article\n");
        free_news_article(article);
        free_news_source(source);
        le_cleanup();
        qzkp_cleanup();
        return 1;
    }
    
    printf("Article signed with post-quantum Falcon signature\n\n");
    
    // 7. Verify the article
    printf("Verifying article integrity and authenticity...\n");
    
    // Verify content integrity through entanglement
    if (verify_article_entanglement(article)) {
        printf("Article content integrity verified through logical entanglement\n");
    } else {
        fprintf(stderr, "Article content integrity verification failed\n");
        free_news_article(article);
        free_news_source(source);
        le_cleanup();
        qzkp_cleanup();
        return 1;
    }
    
    // Verify signature authenticity
    if (verify_article_signature(article, source)) {
        printf("Article signature verified successfully\n");
    } else {
        fprintf(stderr, "Article signature verification failed\n");
        free_news_article(article);
        free_news_source(source);
        le_cleanup();
        qzkp_cleanup();
        return 1;
    }
    
    printf("\n");
    
    // 8. Test tampering detection
    printf("Testing tampering detection...\n");
    
    // Create a tampered copy of the article
    news_article_t* tampered_article = create_news_article(
        "Major Political Development in International Relations",
        "This is a TAMPERED VERSION of the story about diplomatic negotiations between "
        "two major world powers. The content has been MODIFIED to include false information.",
        "Global News Network",
        "Jane Smith",
        "New York, USA"
    );
    
    if (!tampered_article) {
        fprintf(stderr, "Failed to create tampered article\n");
        free_news_article(article);
        free_news_source(source);
        le_cleanup();
        qzkp_cleanup();
        return 1;
    }
    
    // Copy the entanglement hash from the original article
    tampered_article->entanglement_hash_size = article->entanglement_hash_size;
    tampered_article->entanglement_hash = (uint8_t*)malloc(tampered_article->entanglement_hash_size);
    if (!tampered_article->entanglement_hash) {
        fprintf(stderr, "Memory allocation failed for tampered article\n");
        free_news_article(tampered_article);
        free_news_article(article);
        free_news_source(source);
        le_cleanup();
        qzkp_cleanup();
        return 1;
    }
    
    memcpy(tampered_article->entanglement_hash, article->entanglement_hash, tampered_article->entanglement_hash_size);
    
    // Copy the signature from the original article
    tampered_article->signature_size = article->signature_size;
    tampered_article->signature = (uint8_t*)malloc(tampered_article->signature_size);
    if (!tampered_article->signature) {
        fprintf(stderr, "Memory allocation failed for tampered article signature\n");
        free_news_article(tampered_article);
        free_news_article(article);
        free_news_source(source);
        le_cleanup();
        qzkp_cleanup();
        return 1;
    }
    
    memcpy(tampered_article->signature, article->signature, tampered_article->signature_size);
    
    // Verify the tampered article
    if (!verify_article_entanglement(tampered_article)) {
        printf("Tampering correctly detected through logical entanglement verification!\n");
    } else {
        fprintf(stderr, "ERROR: Tampered article passed entanglement verification\n");
    }
    
    if (!verify_article_signature(tampered_article, source)) {
        printf("Tampering correctly detected through signature verification!\n");
    } else {
        fprintf(stderr, "ERROR: Tampered article passed signature verification\n");
    }
    
    printf("\n");
    
    // 9. Test post-quantum key exchange for secure content access
    printf("Testing post-quantum key exchange for secure content access...\n");
    if (simulate_secure_key_exchange(article) == 0) {
        printf("Post-quantum key exchange successful\n");
    } else {
        fprintf(stderr, "Post-quantum key exchange failed\n");
    }
    
    printf("\n");
    
    // Clean up resources
    printf("Cleaning up resources...\n");
    free_news_article(article);
    free_news_article(tampered_article);
    free_news_source(source);
    le_cleanup();
    qzkp_cleanup();
    
    printf("Full cryptographic test completed successfully!\n");
    return 0;
}
