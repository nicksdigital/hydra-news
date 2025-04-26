/**
 * logical_entanglement.h
 * 
 * Header for the logical entanglement system, providing tamper-resistance
 * through interdependencies between proof elements.
 */

#ifndef LOGICAL_ENTANGLEMENT_H
#define LOGICAL_ENTANGLEMENT_H

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

/**
 * Entanglement node structure for creating dependency graphs
 */
typedef struct entanglement_node {
    void* data;                       // Node data
    size_t data_size;                 // Size of data in bytes
    uint8_t* hash;                    // Node hash
    size_t hash_size;                 // Size of hash in bytes
    struct entanglement_node** deps;  // Dependencies
    size_t dep_count;                 // Number of dependencies
} entanglement_node_t;

/**
 * Entanglement graph structure
 */
typedef struct {
    entanglement_node_t** nodes;      // Array of nodes
    size_t node_count;                // Number of nodes
    uint8_t* root_hash;               // Root hash of the graph
    size_t hash_size;                 // Size of hash in bytes
} entanglement_graph_t;

/**
 * Initialize the logical entanglement system
 * 
 * @return 0 on success, error code otherwise
 */
int le_init(void);

/**
 * Create a new entanglement node
 * 
 * @param data Node data
 * @param data_size Size of data in bytes
 * @return Created node or NULL on failure
 */
entanglement_node_t* le_create_node(
    const void* data,
    size_t data_size
);

/**
 * Add a dependency between nodes
 * 
 * @param node Node to add dependency to
 * @param dependency Dependency node
 * @return 0 on success, error code otherwise
 */
int le_add_dependency(
    entanglement_node_t* node,
    entanglement_node_t* dependency
);

/**
 * Create an entanglement graph from nodes
 * 
 * @param nodes Array of nodes
 * @param node_count Number of nodes
 * @return Created graph or NULL on failure
 */
entanglement_graph_t* le_create_graph(
    entanglement_node_t** nodes,
    size_t node_count
);

/**
 * Calculate the entanglement hash for a node
 * 
 * @param node Node to calculate hash for
 * @return 0 on success, error code otherwise
 */
int le_calculate_node_hash(entanglement_node_t* node);

/**
 * Calculate the root hash for an entanglement graph
 * 
 * @param graph Graph to calculate hash for
 * @return 0 on success, error code otherwise
 */
int le_calculate_root_hash(entanglement_graph_t* graph);

/**
 * Verify the integrity of an entanglement graph
 * 
 * @param graph Graph to verify
 * @return true if graph is valid, false otherwise
 */
bool le_verify_graph(const entanglement_graph_t* graph);

/**
 * Verify the integrity of a specific node in the graph
 * 
 * @param node Node to verify
 * @return true if node is valid, false otherwise
 */
bool le_verify_node(const entanglement_node_t* node);

/**
 * Free resources associated with an entanglement node
 * 
 * @param node Node to free
 */
void le_free_node(entanglement_node_t* node);

/**
 * Free resources associated with an entanglement graph
 * 
 * @param graph Graph to free
 */
void le_free_graph(entanglement_graph_t* graph);

/**
 * Clean up the logical entanglement system
 */
void le_cleanup(void);

#endif /* LOGICAL_ENTANGLEMENT_H */
