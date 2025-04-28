package consensus

import (
	"testing"
)

func TestBasicConsensus(t *testing.T) {
	// Create a new consensus network
	network := NewConsensusNetwork()
	if network == nil {
		t.Fatal("Failed to create consensus network")
	}
	
	// Register nodes
	node1 := &Node{
		ID:         "node1",
		PublicKey:  []byte("node1-public-key"),
		Reputation: 1.0,
		Weight:     1.0,
		Specialties: []string{"politics", "economy"},
	}
	
	node2 := &Node{
		ID:         "node2",
		PublicKey:  []byte("node2-public-key"),
		Reputation: 1.0,
		Weight:     1.0,
		Specialties: []string{"science", "technology"},
	}
	
	node3 := &Node{
		ID:         "node3",
		PublicKey:  []byte("node3-public-key"),
		Reputation: 1.0,
		Weight:     1.0,
		Specialties: []string{"sports", "entertainment"},
	}
	
	// Register nodes
	if err := network.RegisterNode(node1); err != nil {
		t.Fatalf("Failed to register node1: %v", err)
	}
	
	if err := network.RegisterNode(node2); err != nil {
		t.Fatalf("Failed to register node2: %v", err)
	}
	
	if err := network.RegisterNode(node3); err != nil {
		t.Fatalf("Failed to register node3: %v", err)
	}
	
	t.Log("Registered 3 nodes successfully")
	
	// Create a content hash
	var contentHash ContentHash
	copy(contentHash[:], []byte("test-content-hash"))
	
	// Submit verifications
	if err := network.SubmitVerification(
		"node1",
		contentHash,
		VerificationLevelStandard,
		[]ContentHash{},
		false,
		[]string{},
	); err != nil {
		t.Fatalf("Failed to submit verification from node1: %v", err)
	}
	
	if err := network.SubmitVerification(
		"node2",
		contentHash,
		VerificationLevelHigh,
		[]ContentHash{},
		false,
		[]string{},
	); err != nil {
		t.Fatalf("Failed to submit verification from node2: %v", err)
	}
	
	t.Log("Submitted verifications successfully")
	
	// Check if content is verified
	if !network.IsContentVerified(contentHash) {
		t.Fatal("Content should be verified")
	}
	
	// Get verification result
	result, err := network.GetVerification(contentHash)
	if err != nil {
		t.Fatalf("Failed to get verification result: %v", err)
	}
	
	// Check verification details
	if len(result.VerifiedBy) != 2 {
		t.Fatalf("Expected 2 verifiers, got %d", len(result.VerifiedBy))
	}
	
	if result.Disputed {
		t.Fatal("Content should not be disputed")
	}
	
	// Calculate trust score
	trustScore, err := network.GetTrustScore(contentHash)
	if err != nil {
		t.Fatalf("Failed to get trust score: %v", err)
	}
	
	t.Logf("Trust score: %f", trustScore)
	
	// Test disputed content
	var disputedHash ContentHash
	copy(disputedHash[:], []byte("disputed-content-hash"))
	
	// Submit verification with dispute
	if err := network.SubmitVerification(
		"node1",
		disputedHash,
		VerificationLevelStandard,
		[]ContentHash{},
		true,
		[]string{"Factual inaccuracy", "Source reliability concerns"},
	); err != nil {
		t.Fatalf("Failed to submit disputed verification: %v", err)
	}
	
	if err := network.SubmitVerification(
		"node2",
		disputedHash,
		VerificationLevelStandard,
		[]ContentHash{},
		false,
		[]string{},
	); err != nil {
		t.Fatalf("Failed to submit verification for disputed content: %v", err)
	}
	
	// Get verification result for disputed content
	disputedResult, err := network.GetVerification(disputedHash)
	if err != nil {
		t.Fatalf("Failed to get verification result for disputed content: %v", err)
	}
	
	// Check disputed status
	if !disputedResult.Disputed {
		t.Fatal("Content should be marked as disputed")
	}
	
	if len(disputedResult.DisputeReasons) != 2 {
		t.Fatalf("Expected 2 dispute reasons, got %d", len(disputedResult.DisputeReasons))
	}
	
	// Get verification level
	level, err := network.GetVerificationLevel(disputedHash)
	if err != nil {
		t.Fatalf("Failed to get verification level: %v", err)
	}
	
	// Verification level should be capped for disputed content
	if level > VerificationLevelMinimal {
		t.Fatalf("Disputed content should have verification level capped at %d, got %d", 
			VerificationLevelMinimal, level)
	}
	
	t.Log("Disputed content correctly handled")
	
	// Test with cross-references
	var refHash1 ContentHash
	var refHash2 ContentHash
	copy(refHash1[:], []byte("reference-hash-1"))
	copy(refHash2[:], []byte("reference-hash-2"))
	
	var contentWithRefs ContentHash
	copy(contentWithRefs[:], []byte("content-with-references"))
	
	// Submit verification with cross-references
	if err := network.SubmitVerification(
		"node3",
		contentWithRefs,
		VerificationLevelStandard,
		[]ContentHash{refHash1, refHash2},
		false,
		[]string{},
	); err != nil {
		t.Fatalf("Failed to submit verification with references: %v", err)
	}
	
	// Get related content
	relatedContent, err := network.GetRelatedContent(contentWithRefs)
	if err != nil {
		t.Fatalf("Failed to get related content: %v", err)
	}
	
	if len(relatedContent) != 2 {
		t.Fatalf("Expected 2 related content items, got %d", len(relatedContent))
	}
	
	t.Log("Cross-references correctly handled")
	
	t.Log("All consensus tests passed successfully")
}
