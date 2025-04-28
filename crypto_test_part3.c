// Include the second part
#include "crypto_test_part2.c"

// Function to verify article entanglement
bool verify_article_entanglement(const news_article_t* article) {
    if (!article || !article->entanglement_hash) {
        return false;
    }
    
    // Create content parts for entanglement verification
    void* content_parts[4];
    size_t content_sizes[4];
    
    content_parts[0] = article->headline;
    content_sizes[0] = strlen(article->headline);
    
    content_parts[1] = article->content;
    content_sizes[1] = strlen(article->content);
    
    content_parts[2] = article->source;
    content_sizes[2] = strlen(article->source);
    
    content_parts[3] = article->author;
    content_sizes[3] = strlen(article->author);
    
    // Create entanglement nodes
    entanglement_node_t* nodes[4];
    for (int i = 0; i < 4; i++) {
        nodes[i] = le_create_node(content_parts[i], content_sizes[i]);
        if (!nodes[i]) {
            // Clean up previously created nodes
            for (int j = 0; j < i; j++) {
                le_free_node(nodes[j]);
            }
            return false;
        }
    }
    
    // Create dependencies between nodes (same as in create_article_entanglement)
    le_add_dependency(nodes[1], nodes[0]);
    le_add_dependency(nodes[2], nodes[1]);
    le_add_dependency(nodes[3], nodes[2]);
    le_add_dependency(nodes[3], nodes[0]);
    
    // Calculate node hashes
    for (int i = 0; i < 4; i++) {
        if (le_calculate_node_hash(nodes[i]) != 0) {
            for (int j = 0; j < 4; j++) {
                le_free_node(nodes[j]);
            }
            return false;
        }
    }
    
    // Create entanglement graph
    entanglement_graph_t* graph = le_create_graph(nodes, 4);
    if (!graph) {
        for (int i = 0; i < 4; i++) {
            le_free_node(nodes[i]);
        }
        return false;
    }
    
    // Calculate root hash
    if (le_calculate_root_hash(graph) != 0) {
        le_free_graph(graph);
        return false;
    }
    
    // Compare calculated hash with stored hash
    bool result = (graph->hash_size == article->entanglement_hash_size &&
                 memcmp(graph->root_hash, article->entanglement_hash, graph->hash_size) == 0);
    
    // Clean up graph
    le_free_graph(graph);
    
    return result;
}

// Function to verify source identity
bool verify_source_identity(const news_source_t* source) {
    if (!source || !source->identity_proof) {
        return false;
    }
    
    // Create public info for verification
    char public_info[512];
    snprintf(public_info, sizeof(public_info), "%s:%s", 
             source->name, source->organization);
    
    // Verification parameters
    qzkp_verify_params_t params = {
        .epsilon = 0.01,      // 1% error margin
        .sample_count = 100   // 100 verification samples
    };
    
    // Verify the proof
    return qzkp_verify_proof(
        source->identity_proof,
        public_info, strlen(public_info),
        &params
    );
}

// Function to verify source location
bool verify_source_location(const news_source_t* source) {
    if (!source || !source->location_proof) {
        return false;
    }
    
    // Create public info for verification (only region, not exact coordinates)
    char public_info[256];
    snprintf(public_info, sizeof(public_info), "region:%s", source->region);
    
    // Verification parameters
    qzkp_verify_params_t params = {
        .epsilon = 0.01,      // 1% error margin
        .sample_count = 100   // 100 verification samples
    };
    
    // Verify the proof
    return qzkp_verify_proof(
        source->location_proof,
        public_info, strlen(public_info),
        &params
    );
}

// Function to free source resources
void free_news_source(news_source_t* source) {
    if (!source) {
        return;
    }
    
    free(source->id);
    free(source->name);
    free(source->organization);
    free(source->region);
    free(source->public_key);
    free(source->private_key);
    
    if (source->identity_proof) {
        qzkp_free_proof(source->identity_proof);
    }
    
    if (source->location_proof) {
        qzkp_free_proof(source->location_proof);
    }
    
    free(source);
}

// Function to free article resources
void free_news_article(news_article_t* article) {
    if (!article) {
        return;
    }
    
    free(article->headline);
    free(article->content);
    free(article->source);
    free(article->author);
    free(article->location);
    free(article->content_hash);
    free(article->entanglement_hash);
    free(article->signature);
    
    free(article);
}

// Function to simulate Kyber key exchange (editor/reader accessing encrypted content)
int simulate_secure_key_exchange(const news_article_t* article) {
    // Generate a keypair for the server (content provider)
    kyber_keypair_t server_keypair;
    if (kyber_keygen(&server_keypair) != 0) {
        fprintf(stderr, "Failed to generate server Kyber keypair\n");
        return -1;
    }
    
    printf("Server Kyber keypair generated successfully\n");
    
    // Client encapsulates a shared secret using server's public key
    uint8_t client_ciphertext[KYBER_CIPHERTEXT_BYTES];
    uint8_t client_shared_secret[KYBER_SHARED_SECRET_BYTES];
    
    if (kyber_encapsulate(client_ciphertext, client_shared_secret, server_keypair.public_key) != 0) {
        fprintf(stderr, "Failed to encapsulate shared secret\n");
        return -1;
    }
    
    printf("Client encapsulated shared secret successfully\n");
    
    // Server decapsulates the shared secret using its secret key
    uint8_t server_shared_secret[KYBER_SHARED_SECRET_BYTES];
    
    if (kyber_decapsulate(server_shared_secret, client_ciphertext, server_keypair.secret_key) != 0) {
        fprintf(stderr, "Failed to decapsulate shared secret\n");
        return -1;
    }
    
    printf("Server decapsulated shared secret successfully\n");
    
    // Verify that both sides have the same shared secret
    if (memcmp(client_shared_secret, server_shared_secret, KYBER_SHARED_SECRET_BYTES) != 0) {
        fprintf(stderr, "Shared secrets do not match\n");
        return -1;
    }
    
    printf("Key exchange successful: both parties have the same shared secret\n");
    return 0;
}
