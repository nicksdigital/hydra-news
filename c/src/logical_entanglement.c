/**
 * logical_entanglement.c
 * 
 * Implementation of the logical entanglement system, providing tamper-resistance
 * through interdependencies between proof elements.
 */

#include "logical_entanglement.h"
#include <stdlib.h>
#include <string.h>
#include <openssl/sha.h>

/* Internal state flag */
static bool is_initialized = false;

/**
 * Initialize the logical entanglement system
 */
int le_init(void) {
    if (is_initialized) {
        return 0;  // Already initialized
    }
    
    is_initialized = true;
    return 0;
}

/**
 * Create a new entanglement node
 */
entanglement_node_t* le_create_node(
    const void* data,
    size_t data_size
) {
    if (!is_initialized || !data || data_size == 0) {
        return NULL;
    }
    
    // Allocate memory for the node
    entanglement_node_t* node = (entanglement_node_t*)malloc(sizeof(entanglement_node_t));
    if (!node) {
        return NULL;
    }
    
    // Allocate memory for data
    node->data = malloc(data_size);
    if (!node->data) {
        free(node);
        return NULL;
    }
    
    // Copy data
    memcpy(node->data, data, data_size);
    node->data_size = data_size;
    
    // Initialize other fields
    node->hash = NULL;
    node->hash_size = 0;
    node->deps = NULL;
    node->dep_count = 0;
    
    return node;
}

/**
 * Add a dependency between nodes
 */
int le_add_dependency(
    entanglement_node_t* node,
    entanglement_node_t* dependency
) {
    if (!is_initialized || !node || !dependency) {
        return -1;
    }
    
    // Resize dependencies array
    entanglement_node_t** new_deps = (entanglement_node_t**)realloc(
        node->deps,
        (node->dep_count + 1) * sizeof(entanglement_node_t*)
    );
    
    if (!new_deps) {
        return -2;
    }
    
    // Add the dependency
    node->deps = new_deps;
    node->deps[node->dep_count] = dependency;
    node->dep_count++;
    
    return 0;
}

/**
 * Create an entanglement graph from nodes
 */
entanglement_graph_t* le_create_graph(
    entanglement_node_t** nodes,
    size_t node_count
) {
    if (!is_initialized || !nodes || node_count == 0) {
        return NULL;
    }
    
    // Allocate graph structure
    entanglement_graph_t* graph = (entanglement_graph_t*)malloc(sizeof(entanglement_graph_t));
    if (!graph) {
        return NULL;
    }
    
    // Allocate nodes array
    graph->nodes = (entanglement_node_t**)malloc(node_count * sizeof(entanglement_node_t*));
    if (!graph->nodes) {
        free(graph);
        return NULL;
    }
    
    // Copy node pointers
    memcpy(graph->nodes, nodes, node_count * sizeof(entanglement_node_t*));
    graph->node_count = node_count;
    
    // Initialize root hash
    graph->root_hash = NULL;
    graph->hash_size = 0;
    
    return graph;
}

/**
 * Calculate the entanglement hash for a node
 */
int le_calculate_node_hash(entanglement_node_t* node) {
    if (!is_initialized || !node || !node->data) {
        return -1;
    }
    
    // Free existing hash if any
    if (node->hash) {
        free(node->hash);
        node->hash = NULL;
        node->hash_size = 0;
    }
    
    // Allocate memory for the hash
    node->hash = (uint8_t*)malloc(SHA256_DIGEST_LENGTH);
    if (!node->hash) {
        return -2;
    }
    
    node->hash_size = SHA256_DIGEST_LENGTH;
    
    // If node has no dependencies, hash the data directly
    if (node->dep_count == 0) {
        SHA256(node->data, node->data_size, node->hash);
        return 0;
    }
    
    // Calculate hashes for dependencies if not already calculated
    for (size_t i = 0; i < node->dep_count; i++) {
        if (!node->deps[i]->hash) {
            int result = le_calculate_node_hash(node->deps[i]);
            if (result != 0) {
                return result;
            }
        }
    }
    
    // Calculate combined hash of data and dependency hashes
    SHA256_CTX ctx;
    if (SHA256_Init(&ctx) != 1) {
        return -3;
    }
    
    // Add node's data
    if (SHA256_Update(&ctx, node->data, node->data_size) != 1) {
        return -3;
    }
    
    // Add dependency hashes
    for (size_t i = 0; i < node->dep_count; i++) {
        if (SHA256_Update(&ctx, node->deps[i]->hash, node->deps[i]->hash_size) != 1) {
            return -3;
        }
    }
    
    // Finalize hash
    if (SHA256_Final(node->hash, &ctx) != 1) {
        return -3;
    }
    
    return 0;
}

/**
 * Calculate the root hash for an entanglement graph
 */
int le_calculate_root_hash(entanglement_graph_t* graph) {
    if (!is_initialized || !graph || !graph->nodes || graph->node_count == 0) {
        return -1;
    }
    
    // Free existing root hash if any
    if (graph->root_hash) {
        free(graph->root_hash);
        graph->root_hash = NULL;
        graph->hash_size = 0;
    }
    
    // Calculate hashes for all nodes
    for (size_t i = 0; i < graph->node_count; i++) {
        if (!graph->nodes[i]->hash) {
            int result = le_calculate_node_hash(graph->nodes[i]);
            if (result != 0) {
                return result;
            }
        }
    }
    
    // Allocate memory for the root hash
    graph->root_hash = (uint8_t*)malloc(SHA256_DIGEST_LENGTH);
    if (!graph->root_hash) {
        return -2;
    }
    
    graph->hash_size = SHA256_DIGEST_LENGTH;
    
    // Calculate combined hash of all node hashes
    SHA256_CTX ctx;
    if (SHA256_Init(&ctx) != 1) {
        return -3;
    }
    
    // Add all node hashes
    for (size_t i = 0; i < graph->node_count; i++) {
        if (SHA256_Update(&ctx, graph->nodes[i]->hash, graph->nodes[i]->hash_size) != 1) {
            return -3;
        }
    }
    
    // Finalize hash
    if (SHA256_Final(graph->root_hash, &ctx) != 1) {
        return -3;
    }
    
    return 0;
}

/**
 * Verify the integrity of an entanglement graph
 */
bool le_verify_graph(const entanglement_graph_t* graph) {
    if (!is_initialized || !graph || !graph->nodes || graph->node_count == 0 || !graph->root_hash) {
        return false;
    }
    
    // Create a temporary graph to recalculate the root hash
    entanglement_graph_t temp_graph;
    temp_graph.nodes = graph->nodes;
    temp_graph.node_count = graph->node_count;
    temp_graph.root_hash = NULL;
    temp_graph.hash_size = 0;
    
    // Calculate the root hash
    int result = le_calculate_root_hash(&temp_graph);
    if (result != 0) {
        if (temp_graph.root_hash) {
            free(temp_graph.root_hash);
        }
        return false;
    }
    
    // Compare the calculated hash with the original
    bool match = (
        graph->hash_size == temp_graph.hash_size &&
        memcmp(graph->root_hash, temp_graph.root_hash, graph->hash_size) == 0
    );
    
    // Free the temporary hash
    free(temp_graph.root_hash);
    
    return match;
}

/**
 * Verify the integrity of a specific node in the graph
 */
bool le_verify_node(const entanglement_node_t* node) {
    if (!is_initialized || !node || !node->data || !node->hash) {
        return false;
    }
    
    // Create a temporary node to recalculate the hash
    entanglement_node_t temp_node;
    temp_node.data = node->data;
    temp_node.data_size = node->data_size;
    temp_node.deps = node->deps;
    temp_node.dep_count = node->dep_count;
    temp_node.hash = NULL;
    temp_node.hash_size = 0;
    
    // Calculate the node hash
    int result = le_calculate_node_hash(&temp_node);
    if (result != 0) {
        if (temp_node.hash) {
            free(temp_node.hash);
        }
        return false;
    }
    
    // Compare the calculated hash with the original
    bool match = (
        node->hash_size == temp_node.hash_size &&
        memcmp(node->hash, temp_node.hash, node->hash_size) == 0
    );
    
    // Free the temporary hash
    free(temp_node.hash);
    
    return match;
}

/**
 * Free resources associated with an entanglement node
 */
void le_free_node(entanglement_node_t* node) {
    if (!node) {
        return;
    }
    
    // Free data
    if (node->data) {
        free(node->data);
    }
    
    // Free hash
    if (node->hash) {
        free(node->hash);
    }
    
    // Free dependencies array (but not the dependent nodes themselves)
    if (node->deps) {
        free(node->deps);
    }
    
    // Free the node
    free(node);
}

/**
 * Free resources associated with an entanglement graph
 */
void le_free_graph(entanglement_graph_t* graph) {
    if (!graph) {
        return;
    }
    
    // Free root hash
    if (graph->root_hash) {
        free(graph->root_hash);
    }
    
    // Free nodes array (but not the nodes themselves)
    if (graph->nodes) {
        free(graph->nodes);
    }
    
    // Free the graph
    free(graph);
}

/**
 * Clean up the logical entanglement system
 */
void le_cleanup(void) {
    is_initialized = false;
}
