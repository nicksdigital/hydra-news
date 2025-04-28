#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../include/logical_entanglement.h"

int main() {
    printf("Testing Logical Entanglement Implementation\n");
    
    // Initialize the logical entanglement system
    if (le_init() != 0) {
        printf("Failed to initialize logical entanglement system\n");
        return 1;
    }
    
    printf("Logical entanglement system initialized successfully\n");
    
    // Create test data
    const char *data1 = "First piece of content that should be entangled";
    const char *data2 = "Second piece of content with logical dependencies";
    const char *data3 = "Third piece of content that forms part of the graph";
    
    // Create nodes
    entanglement_node_t *node1 = le_create_node(data1, strlen(data1));
    entanglement_node_t *node2 = le_create_node(data2, strlen(data2));
    entanglement_node_t *node3 = le_create_node(data3, strlen(data3));
    
    if (node1 == NULL || node2 == NULL || node3 == NULL) {
        printf("Failed to create entanglement nodes\n");
        le_cleanup();
        return 1;
    }
    
    printf("Created 3 entanglement nodes successfully\n");
    
    // Add dependencies between nodes
    if (le_add_dependency(node2, node1) != 0) {
        printf("Failed to add dependency from node2 to node1\n");
        le_cleanup();
        return 1;
    }
    
    if (le_add_dependency(node3, node1) != 0 || 
        le_add_dependency(node3, node2) != 0) {
        printf("Failed to add dependencies to node3\n");
        le_cleanup();
        return 1;
    }
    
    printf("Added dependencies between nodes successfully\n");
    
    // Calculate node hashes
    if (le_calculate_node_hash(node1) != 0 ||
        le_calculate_node_hash(node2) != 0 ||
        le_calculate_node_hash(node3) != 0) {
        printf("Failed to calculate node hashes\n");
        le_cleanup();
        return 1;
    }
    
    printf("Calculated node hashes successfully\n");
    
    // Create entanglement graph
    entanglement_node_t *nodes[] = {node1, node2, node3};
    entanglement_graph_t *graph = le_create_graph(nodes, 3);
    
    if (graph == NULL) {
        printf("Failed to create entanglement graph\n");
        le_cleanup();
        return 1;
    }
    
    printf("Created entanglement graph successfully\n");
    
    // Calculate root hash
    if (le_calculate_root_hash(graph) != 0) {
        printf("Failed to calculate root hash\n");
        le_cleanup();
        return 1;
    }
    
    printf("Calculated root hash successfully\n");
    
    // Verify graph integrity
    if (le_verify_graph(graph)) {
        printf("Graph verification successful\n");
    } else {
        printf("Graph verification failed\n");
    }
    
    // Test tampering detection
    printf("Testing tampering detection...\n");
    
    // Tamper with node1 data
    char *tampered_data = strdup(data1);
    tampered_data[10] = 'X'; // Change a character
    memcpy(node1->data, tampered_data, strlen(tampered_data));
    
    // Verify graph integrity after tampering
    if (le_verify_graph(graph)) {
        printf("ERROR: Graph verification passed after tampering!\n");
    } else {
        printf("Tampering correctly detected: graph verification failed after tampering\n");
    }
    
    free(tampered_data);
    
    // Clean up
    le_free_graph(graph);
    le_cleanup();
    
    printf("Logical entanglement test completed\n");
    return 0;
}
