// Include the first part header
#include "crypto_test_part1.c"

// Function to create a news article
news_article_t* create_news_article(const char* headline, const char* content, 
                                 const char* source, const char* author,
                                 const char* location) {
    news_article_t* article = (news_article_t*)malloc(sizeof(news_article_t));
    if (!article) {
        return NULL;
    }
    
    // Set basic article information
    article->headline = strdup(headline);
    article->content = strdup(content);
    article->source = strdup(source);
    article->author = strdup(author);
    article->location = strdup(location);
    article->timestamp = time(NULL);
    
    // Initialize hashes and signature to NULL (will be generated later)
    article->content_hash = NULL;
    article->hash_size = 0;
    article->entanglement_hash = NULL;
    article->entanglement_hash_size = 0;
    article->signature = NULL;
    article->signature_size = 0;
    
    return article;
}

// Function to create logical entanglement for article content
int create_article_entanglement(news_article_t* article) {
    if (!article) {
        return -1;
    }
    
    // Create content parts for entanglement
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
            return -1;
        }
    }
    
    // Create dependencies between nodes
    // Headline depends on nothing
    // Content depends on headline
    le_add_dependency(nodes[1], nodes[0]);
    // Source depends on content
    le_add_dependency(nodes[2], nodes[1]);
    // Author depends on source and headline
    le_add_dependency(nodes[3], nodes[2]);
    le_add_dependency(nodes[3], nodes[0]);
    
    // Calculate node hashes
    for (int i = 0; i < 4; i++) {
        if (le_calculate_node_hash(nodes[i]) != 0) {
            for (int j = 0; j < 4; j++) {
                le_free_node(nodes[j]);
            }
            return -1;
        }
    }
    
    // Create entanglement graph
    entanglement_graph_t* graph = le_create_graph(nodes, 4);
    if (!graph) {
        for (int i = 0; i < 4; i++) {
            le_free_node(nodes[i]);
        }
        return -1;
    }
    
    // Calculate root hash
    if (le_calculate_root_hash(graph) != 0) {
        le_free_graph(graph);
        return -1;
    }
    
    // Store entanglement hash
    article->entanglement_hash_size = graph->hash_size;
    article->entanglement_hash = (uint8_t*)malloc(article->entanglement_hash_size);
    if (!article->entanglement_hash) {
        le_free_graph(graph);
        return -1;
    }
    
    memcpy(article->entanglement_hash, graph->root_hash, article->entanglement_hash_size);
    
    // Clean up graph
    le_free_graph(graph);
    
    return 0;
}

// Function to sign an article with source's private key
int sign_article(news_article_t* article, const news_source_t* source) {
    if (!article || !source || !source->private_key) {
        return -1;
    }
    
    // Create message to sign (headline + entanglement hash)
    size_t msg_size = strlen(article->headline) + article->entanglement_hash_size;
    uint8_t* message = (uint8_t*)malloc(msg_size);
    if (!message) {
        return -1;
    }
    
    memcpy(message, article->headline, strlen(article->headline));
    memcpy(message + strlen(article->headline), article->entanglement_hash, article->entanglement_hash_size);
    
    // Allocate space for signature
    article->signature = (uint8_t*)malloc(FALCON_SIGNATURE_BYTES);
    if (!article->signature) {
        free(message);
        return -1;
    }
    
    // Sign the message
    unsigned long long sig_len;
    int result = falcon_sign(
        article->signature, &sig_len,
        message, msg_size,
        source->private_key
    );
    
    article->signature_size = sig_len;
    
    free(message);
    return result;
}

// Function to verify article signature
bool verify_article_signature(const news_article_t* article, const news_source_t* source) {
    if (!article || !source || !source->public_key || !article->signature) {
        return false;
    }
    
    // Recreate message (headline + entanglement hash)
    size_t msg_size = strlen(article->headline) + article->entanglement_hash_size;
    uint8_t* message = (uint8_t*)malloc(msg_size);
    if (!message) {
        return false;
    }
    
    memcpy(message, article->headline, strlen(article->headline));
    memcpy(message + strlen(article->headline), article->entanglement_hash, article->entanglement_hash_size);
    
    // Verify the signature
    int result = falcon_verify(
        message, msg_size,
        article->signature, article->signature_size,
        source->public_key
    );
    
    free(message);
    return (result == 0);
}
