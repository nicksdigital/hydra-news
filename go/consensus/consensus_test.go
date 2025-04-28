package consensus

import (
	"context"
	"fmt"
	"sync"
	"testing"
	"time"
)

// TestConsensusBasic tests basic consensus functionality
func TestConsensusBasic(t *testing.T) {
	// Create a network with 4 nodes
	network := NewConsensusNetwork()
	
	// Add 4 nodes
	for i := 1; i <= 4; i++ {
		nodeName := fmt.Sprintf("node%d", i)
		node := NewConsensusNode(nodeName)
		network.AddNode(node)
	}
	
	// Connect the nodes in a fully connected topology
	network.ConnectAllNodes()
	
	// Propose a value on the first node
	proposedValue := []byte("test-value")
	err := network.nodes[0].ProposeValue(context.Background(), proposedValue)
	if err != nil {
		t.Fatalf("Failed to propose value: %v", err)
	}
	
	// Wait for consensus to be reached
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	
	consensusReached := make(chan bool, 1)
	go func() {
		for {
			if network.IsConsensusReached(proposedValue) {
				consensusReached <- true
				return
			}
			
			select {
			case <-ctx.Done():
				return
			case <-time.After(100 * time.Millisecond):
				// Keep checking
			}
		}
	}()
	
	select {
	case <-consensusReached:
		// Success
	case <-ctx.Done():
		t.Fatalf("Consensus was not reached within timeout")
	}
	
	// Verify that all nodes have the same value
	for i, node := range network.nodes {
		value, err := node.GetConsensusValue()
		if err != nil {
			t.Fatalf("Node %d failed to get consensus value: %v", i, err)
		}
		
		if string(value) != string(proposedValue) {
			t.Errorf("Node %d has incorrect consensus value. Expected: %s, Got: %s", 
				i, string(proposedValue), string(value))
		}
	}
}

// TestByzantineFaultTolerance tests the network's ability to reach consensus
// even in the presence of faulty nodes
func TestByzantineFaultTolerance(t *testing.T) {
	// Create a network with 7 nodes (can tolerate up to 2 byzantine failures)
	network := NewConsensusNetwork()
	
	// Add 7 nodes
	for i := 1; i <= 7; i++ {
		nodeName := fmt.Sprintf("node%d", i)
		node := NewConsensusNode(nodeName)
		network.AddNode(node)
	}
	
	// Connect the nodes in a fully connected topology
	network.ConnectAllNodes()
	
	// Mark the last 2 nodes as byzantine (faulty)
	network.nodes[5].SetByzantine(true, "malicious-drop") // This node drops messages
	network.nodes[6].SetByzantine(true, "malicious-alter") // This node alters values
	
	// Propose a value on the first node
	proposedValue := []byte("critical-data")
	err := network.nodes[0].ProposeValue(context.Background(), proposedValue)
	if err != nil {
		t.Fatalf("Failed to propose value: %v", err)
	}
	
	// Wait for consensus to be reached
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	
	consensusReached := make(chan bool, 1)
	go func() {
		for {
			// We only check honest nodes (0-4)
			honest := true
			for i := 0; i < 5; i++ {
				value, err := network.nodes[i].GetConsensusValue()
				if err != nil || string(value) != string(proposedValue) {
					honest = false
					break
				}
			}
			
			if honest {
				consensusReached <- true
				return
			}
			
			select {
			case <-ctx.Done():
				return
			case <-time.After(100 * time.Millisecond):
				// Keep checking
			}
		}
	}()
	
	select {
	case <-consensusReached:
		// Success
	case <-ctx.Done():
		t.Fatalf("Byzantine fault-tolerant consensus was not reached within timeout")
	}
	
	// Verify that all honest nodes have the same value
	for i := 0; i < 5; i++ {
		value, err := network.nodes[i].GetConsensusValue()
		if err != nil {
			t.Fatalf("Honest node %d failed to get consensus value: %v", i, err)
		}
		
		if string(value) != string(proposedValue) {
			t.Errorf("Honest node %d has incorrect consensus value. Expected: %s, Got: %s", 
				i, string(proposedValue), string(value))
		}
	}
	
	// Byzantine nodes might have different values, which is expected
	t.Logf("Byzantine nodes may have different values, which is expected behavior")
}

// TestConcurrentProposals tests the network's ability to handle concurrent proposals
func TestConcurrentProposals(t *testing.T) {
	// Create a network with 5 nodes
	network := NewConsensusNetwork()
	
	// Add 5 nodes
	for i := 1; i <= 5; i++ {
		nodeName := fmt.Sprintf("node%d", i)
		node := NewConsensusNode(nodeName)
		network.AddNode(node)
	}
	
	// Connect the nodes in a fully connected topology
	network.ConnectAllNodes()
	
	// Propose values concurrently from different nodes
	var wg sync.WaitGroup
	proposedValues := make([][]byte, 3)
	
	for i := 0; i < 3; i++ {
		wg.Add(1)
		go func(idx int) {
			defer wg.Done()
			proposedValues[idx] = []byte(fmt.Sprintf("concurrent-value-%d", idx))
			err := network.nodes[idx].ProposeValue(context.Background(), proposedValues[idx])
			if err != nil {
				t.Errorf("Failed to propose value from node %d: %v", idx, err)
			}
		}(i)
	}
	
	wg.Wait()
	
	// Wait for consensus to be reached
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	
	time.Sleep(5 * time.Second) // Give some time for the consensus to be reached
	
	// Verify that all nodes have the same value
	consensusValue, err := network.nodes[0].GetConsensusValue()
	if err != nil {
		t.Fatalf("Failed to get consensus value: %v", err)
	}
	
	for i, node := range network.nodes {
		value, err := node.GetConsensusValue()
		if err != nil {
			t.Fatalf("Node %d failed to get consensus value: %v", i, err)
		}
		
		if string(value) != string(consensusValue) {
			t.Errorf("Node %d has incorrect consensus value. Expected: %s, Got: %s", 
				i, string(consensusValue), string(value))
		}
	}
	
	// Check that the consensus value is one of the proposed values
	found := false
	for _, val := range proposedValues {
		if string(consensusValue) == string(val) {
			found = true
			break
		}
	}
	
	if !found {
		t.Errorf("Consensus value %s is not one of the proposed values", string(consensusValue))
	}
}

// TestNetworkPartition tests the network's behavior when the network is partitioned
func TestNetworkPartition(t *testing.T) {
	// Create a network with 6 nodes
	network := NewConsensusNetwork()
	
	// Add 6 nodes
	for i := 1; i <= 6; i++ {
		nodeName := fmt.Sprintf("node%d", i)
		node := NewConsensusNode(nodeName)
		network.AddNode(node)
	}
	
	// Create two partitions: nodes 0-2 and nodes 3-5
	for i := 0; i < 3; i++ {
		for j := 0; j < 3; j++ {
			network.ConnectNodes(i, j)
			network.ConnectNodes(i+3, j+3)
		}
	}
	
	// Propose different values in each partition
	partition1Value := []byte("partition1-value")
	partition2Value := []byte("partition2-value")
	
	err1 := network.nodes[0].ProposeValue(context.Background(), partition1Value)
	if err1 != nil {
		t.Fatalf("Failed to propose value in partition 1: %v", err1)
	}
	
	err2 := network.nodes[3].ProposeValue(context.Background(), partition2Value)
	if err2 != nil {
		t.Fatalf("Failed to propose value in partition 2: %v", err2)
	}
	
	// Give time for consensus to be reached within partitions
	time.Sleep(5 * time.Second)
	
	// Verify that nodes in each partition have reached consensus within their partition
	for i := 0; i < 3; i++ {
		value, err := network.nodes[i].GetConsensusValue()
		if err != nil {
			t.Fatalf("Node %d in partition 1 failed to get consensus value: %v", i, err)
		}
		
		if string(value) != string(partition1Value) {
			t.Errorf("Node %d in partition 1 has incorrect consensus value. Expected: %s, Got: %s", 
				i, string(partition1Value), string(value))
		}
	}
	
	for i := 3; i < 6; i++ {
		value, err := network.nodes[i].GetConsensusValue()
		if err != nil {
			t.Fatalf("Node %d in partition 2 failed to get consensus value: %v", i, err)
		}
		
		if string(value) != string(partition2Value) {
			t.Errorf("Node %d in partition 2 has incorrect consensus value. Expected: %s, Got: %s", 
				i, string(partition2Value), string(value))
		}
	}
	
	// Now heal the partition by connecting nodes between partitions
	for i := 0; i < 3; i++ {
		for j := 3; j < 6; j++ {
			network.ConnectNodes(i, j)
		}
	}
	
	// Force a new proposal to trigger consensus across the healed network
	healedNetworkValue := []byte("healed-network-value")
	err := network.nodes[2].ProposeValue(context.Background(), healedNetworkValue)
	if err != nil {
		t.Fatalf("Failed to propose value in healed network: %v", err)
	}
	
	// Wait for consensus to be reached across the entire network
	time.Sleep(5 * time.Second)
	
	// Verify that all nodes have the same value
	for i, node := range network.nodes {
		value, err := node.GetConsensusValue()
		if err != nil {
			t.Fatalf("Node %d failed to get consensus value: %v", i, err)
		}
		
		if string(value) != string(healedNetworkValue) {
			t.Errorf("Node %d has incorrect consensus value after healing. Expected: %s, Got: %s", 
				i, string(healedNetworkValue), string(value))
		}
	}
}

// TestLargeNetworkScalability tests the network's ability to scale with many nodes
func TestLargeNetworkScalability(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping large network test in short mode")
	}
	
	// Create a network with 20 nodes
	network := NewConsensusNetwork()
	
	// Add 20 nodes
	for i := 1; i <= 20; i++ {
		nodeName := fmt.Sprintf("node%d", i)
		node := NewConsensusNode(nodeName)
		network.AddNode(node)
	}
	
	// Connect the nodes in a ring topology (less connections than fully connected)
	for i := 0; i < 20; i++ {
		network.ConnectNodes(i, (i+1)%20)  // Connect to next node
		network.ConnectNodes(i, (i+2)%20)  // Connect to node after next
	}
	
	// Propose a value
	proposedValue := []byte("scalability-test-value")
	err := network.nodes[0].ProposeValue(context.Background(), proposedValue)
	if err != nil {
		t.Fatalf("Failed to propose value: %v", err)
	}
	
	// Wait for consensus to be reached
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()
	
	start := time.Now()
	
	consensusReached := make(chan bool, 1)
	go func() {
		for {
			if network.IsConsensusReached(proposedValue) {
				consensusReached <- true
				return
			}
			
			select {
			case <-ctx.Done():
				return
			case <-time.After(500 * time.Millisecond):
				// Keep checking
			}
		}
	}()
	
	select {
	case <-consensusReached:
		elapsed := time.Since(start)
		t.Logf("Consensus reached in %v for a 20-node network", elapsed)
	case <-ctx.Done():
		t.Fatalf("Consensus was not reached within timeout")
	}
	
	// Verify that all nodes have the same value
	for i, node := range network.nodes {
		value, err := node.GetConsensusValue()
		if err != nil {
			t.Fatalf("Node %d failed to get consensus value: %v", i, err)
		}
		
		if string(value) != string(proposedValue) {
			t.Errorf("Node %d has incorrect consensus value. Expected: %s, Got: %s", 
				i, string(proposedValue), string(value))
		}
	}
}

// TestSourceAuthenticity tests the system's ability to verify source authenticity
func TestSourceAuthenticity(t *testing.T) {
	// Create a network with 4 nodes
	network := NewConsensusNetwork()
	
	// Add 4 nodes
	for i := 1; i <= 4; i++ {
		nodeName := fmt.Sprintf("node%d", i)
		node := NewConsensusNode(nodeName)
		network.AddNode(node)
	}
	
	// Connect the nodes in a fully connected topology
	network.ConnectAllNodes()
	
	// Create a source with a keypair
	sourceID := "trusted-journalist"
	sourceKeypair, err := GenerateSourceKeypair(sourceID)
	if err != nil {
		t.Fatalf("Failed to generate source keypair: %v", err)
	}
	
	// Register the source with all nodes
	for _, node := range network.nodes {
		err := node.RegisterSource(sourceID, sourceKeypair.PublicKey)
		if err != nil {
			t.Fatalf("Failed to register source with node: %v", err)
		}
	}
	
	// Create a message and sign it with the source's private key
	message := []byte("authenticated-news-content")
	signature, err := SignMessage(message, sourceKeypair.PrivateKey)
	if err != nil {
		t.Fatalf("Failed to sign message: %v", err)
	}
	
	// Verify the signature on all nodes
	for i, node := range network.nodes {
		valid, err := node.VerifySourceSignature(sourceID, message, signature)
		if err != nil {
			t.Fatalf("Node %d failed to verify signature: %v", i, err)
		}
		
		if !valid {
			t.Errorf("Node %d reported signature as invalid", i)
		}
	}
	
	// Test with tampered message
	tamperedMessage := append([]byte{}, message...)
	tamperedMessage[0] ^= 0x01
	
	for i, node := range network.nodes {
		valid, err := node.VerifySourceSignature(sourceID, tamperedMessage, signature)
		if err != nil {
			// An error might be expected here
			continue
		}
		
		if valid {
			t.Errorf("Node %d verified signature for tampered message", i)
		}
	}
	
	// Test with fake source ID
	fakeSourceID := "fake-journalist"
	for i, node := range network.nodes {
		valid, err := node.VerifySourceSignature(fakeSourceID, message, signature)
		if err != nil {
			// An error might be expected here
			continue
		}
		
		if valid {
			t.Errorf("Node %d verified signature for fake source ID", i)
		}
	}
}

// TestGeolocationVerification tests the system's ability to verify source locations
// while protecting exact coordinates
func TestGeolocationVerification(t *testing.T) {
	// Create a network with 4 nodes
	network := NewConsensusNetwork()
	
	// Add 4 nodes
	for i := 1; i <= 4; i++ {
		nodeName := fmt.Sprintf("node%d", i)
		node := NewConsensusNode(nodeName)
		network.AddNode(node)
	}
	
	// Connect the nodes in a fully connected topology
	network.ConnectAllNodes()
	
	// Define a source with actual coordinates (these would be private in real system)
	sourceID := "field-journalist"
	actualLat := 40.7128  // NYC latitude
	actualLong := -74.0060 // NYC longitude
	
	// Generate a zero-knowledge proof for location within North America
	regionBoundaries := [][]float64{
		{24.396308, -125.000000}, // Southwest corner
		{49.384358, -66.934570},  // Northeast corner
	}
	
	locationProof, err := GenerateLocationProof(sourceID, actualLat, actualLong, regionBoundaries)
	if err != nil {
		t.Fatalf("Failed to generate location proof: %v", err)
	}
	
	// Verify the location proof on all nodes
	for i, node := range network.nodes {
		valid, region, err := node.VerifyLocationProof(locationProof)
		if err != nil {
			t.Fatalf("Node %d failed to verify location proof: %v", i, err)
		}
		
		if !valid {
			t.Errorf("Node %d reported location proof as invalid", i)
		}
		
		if region != "North America" {
			t.Errorf("Node %d reported incorrect region: %s", i, region)
		}
	}
	
	// Test with location outside the claimed region
	outsideLat := 51.5074  // London latitude
	outsideLong := -0.1278 // London longitude
	
	invalidLocationProof, err := GenerateLocationProof(sourceID, outsideLat, outsideLong, regionBoundaries)
	if err != nil {
		t.Fatalf("Failed to generate invalid location proof: %v", err)
	}
	
	// This should fail verification or report different region
	for i, node := range network.nodes {
		valid, region, err := node.VerifyLocationProof(invalidLocationProof)
		if err == nil && valid && region == "North America" {
			t.Errorf("Node %d incorrectly verified location proof for point outside region", i)
		}
	}
}

// TestNewsEntanglement tests the logical entanglement of news content
func TestNewsEntanglement(t *testing.T) {
	// Create a simulated news content structure
	contentParts := [][]byte{
		[]byte("HEADLINE: Breaking News on Elections"),
		[]byte("SUMMARY: Election results show unexpected outcomes in key regions"),
		[]byte("CONTENT: Detailed analysis of voting patterns reveals..."),
		[]byte("SOURCES: Multiple independent observers confirmed..."),
		[]byte("METADATA: Timestamp, Location, Reporter ID"),
	}
	
	// Create logical entanglement for the content parts
	entanglement, err := CreateNewsEntanglement(contentParts)
	if err != nil {
		t.Fatalf("Failed to create news entanglement: %v", err)
	}
	
	// Verify the entanglement is valid
	valid, err := VerifyNewsEntanglement(contentParts, entanglement)
	if err != nil {
		t.Fatalf("Failed to verify news entanglement: %v", err)
	}
	
	if !valid {
		t.Errorf("News entanglement verification failed")
	}
	
	// Test tampering with one part of the content
	tamperedContent := make([][]byte, len(contentParts))
	copy(tamperedContent, contentParts)
	tamperedContent[2] = []byte("CONTENT: Modified analysis of voting patterns reveals different conclusions...")
	
	valid, err = VerifyNewsEntanglement(tamperedContent, entanglement)
	if err != nil {
		t.Logf("Expected error when verifying tampered content: %v", err)
	}
	
	if valid {
		t.Errorf("Tampered news content incorrectly verified as valid")
	}
	
	// Test with partial content (missing parts)
	partialContent := contentParts[:3]
	valid, err = VerifyNewsEntanglement(partialContent, entanglement)
	if err != nil {
		t.Logf("Expected error when verifying partial content: %v", err)
	}
	
	if valid {
		t.Errorf("Partial news content incorrectly verified as valid")
	}
}

// TestCompleteNewsVerificationFlow tests the end-to-end flow of the news verification system
func TestCompleteNewsVerificationFlow(t *testing.T) {
	// Create a network with 4 nodes
	network := NewConsensusNetwork()
	
	// Add 4 nodes
	for i := 1; i <= 4; i++ {
		nodeName := fmt.Sprintf("node%d", i)
		node := NewConsensusNode(nodeName)
		network.AddNode(node)
	}
	
	// Connect the nodes in a fully connected topology
	network.ConnectAllNodes()
	
	// 1. Create a source identity with location proof
	sourceID := "field-reporter-123"
	sourceKeypair, err := GenerateSourceKeypair(sourceID)
	if err != nil {
		t.Fatalf("Failed to generate source keypair: %v", err)
	}
	
	// Register the source with all nodes
	for _, node := range network.nodes {
		err := node.RegisterSource(sourceID, sourceKeypair.PublicKey)
		if err != nil {
			t.Fatalf("Failed to register source with node: %v", err)
		}
	}
	
	// 2. Generate a location proof
	regionBoundaries := [][]float64{
		{24.396308, -125.000000}, // Southwest corner of North America
		{49.384358, -66.934570},  // Northeast corner of North America
	}
	locationProof, err := GenerateLocationProof(sourceID, 40.7128, -74.0060, regionBoundaries)
	if err != nil {
		t.Fatalf("Failed to generate location proof: %v", err)
	}
	
	// 3. Create news content
	contentParts := [][]byte{
		[]byte("HEADLINE: Major Political Development"),
		[]byte("SUMMARY: Key legislation passed with bipartisan support"),
		[]byte("CONTENT: After months of negotiation, the comprehensive bill was finally..."),
		[]byte("SOURCES: According to official parliamentary records and statements..."),
		[]byte("METADATA: 2023-09-21T15:30:00Z, North America, field-reporter-123"),
	}
	
	// 4. Create logical entanglement for the content
	entanglement, err := CreateNewsEntanglement(contentParts)
	if err != nil {
		t.Fatalf("Failed to create news entanglement: %v", err)
	}
	
	// 5. Sign the news content and entanglement
	contentHash := ComputeContentHash(contentParts)
	signature, err := SignMessage(append(contentHash, entanglement.RootHash...), sourceKeypair.PrivateKey)
	if err != nil {
		t.Fatalf("Failed to sign news content: %v", err)
	}
	
	// 6. Create a complete news verification package
	verificationPackage := NewsVerificationPackage{
		SourceID:      sourceID,
		Content:       contentParts,
		Entanglement:  entanglement,
		Signature:     signature,
		LocationProof: locationProof,
		Timestamp:     time.Now(),
	}
	
	// 7. Submit the package to the consensus network
	err = network.nodes[0].ProposeNewsVerification(context.Background(), verificationPackage)
	if err != nil {
		t.Fatalf("Failed to propose news verification: %v", err)
	}
	
	// 8. Wait for consensus to be reached
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	
	consensusReached := make(chan bool, 1)
	go func() {
		for {
			// Check if all nodes have verified the news
			allVerified := true
			for _, node := range network.nodes {
				verified, err := node.IsNewsVerified(contentHash)
				if err != nil || !verified {
					allVerified = false
					break
				}
			}
			
			if allVerified {
				consensusReached <- true
				return
			}
			
			select {
			case <-ctx.Done():
				return
			case <-time.After(500 * time.Millisecond):
				// Keep checking
			}
		}
	}()
	
	select {
	case <-consensusReached:
		// Success
	case <-ctx.Done():
		t.Fatalf("News verification consensus was not reached within timeout")
	}
	
	// 9. Verify the results on all nodes
	for i, node := range network.nodes {
		// Check if the news content is verified
		verified, err := node.IsNewsVerified(contentHash)
		if err != nil {
			t.Fatalf("Node %d failed to check news verification: %v", i, err)
		}
		
		if !verified {
			t.Errorf("Node %d did not verify the news content", i)
		}
		
		// Check the verification details
		details, err := node.GetNewsVerificationDetails(contentHash)
		if err != nil {
			t.Fatalf("Node %d failed to get verification details: %v", i, err)
		}
		
		if details.SourceID != sourceID {
			t.Errorf("Node %d has incorrect source ID: %s", i, details.SourceID)
		}
		
		if details.Region != "North America" {
			t.Errorf("Node %d has incorrect region: %s", i, details.Region)
		}
		
		if !details.ContentIntact {
			t.Errorf("Node %d reports content as not intact", i)
		}
		
		if !details.SourceAuthentic {
			t.Errorf("Node %d reports source as not authentic", i)
		}
	}
	
	// 10. Test with tampered content
	tamperedPackage := verificationPackage
	tamperedPackage.Content = make([][]byte, len(contentParts))
	copy(tamperedPackage.Content, contentParts)
	tamperedPackage.Content[2] = []byte("CONTENT: Completely different information that was not in the original...")
	
	err = network.nodes[1].ProposeNewsVerification(context.Background(), tamperedPackage)
	if err != nil {
		t.Logf("Expected error when proposing tampered news: %v", err)
	}
	
	// The tampered content should not be verified
	time.Sleep(3 * time.Second)
	
	tamperedHash := ComputeContentHash(tamperedPackage.Content)
	for i, node := range network.nodes {
		verified, err := node.IsNewsVerified(tamperedHash)
		if err == nil && verified {
			t.Errorf("Node %d incorrectly verified tampered news content", i)
		}
	}
}
