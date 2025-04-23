// Package consensus implements the distributed consensus network
// for Hydra News, providing secure verification of news content.
package consensus

import (
	"crypto/sha256"
	"encoding/hex"
	"errors"
	"sync"
	"time"
)

// Verification levels for content
const (
	VerificationLevelNone     = 0
	VerificationLevelMinimal  = 1
	VerificationLevelStandard = 2
	VerificationLevelHigh     = 3
	VerificationLevelMaximum  = 4
)

// ContentHash represents a cryptographic hash of content
type ContentHash [32]byte

// String returns the hex representation of a ContentHash
func (h ContentHash) String() string {
	return hex.EncodeToString(h[:])
}

// VerificationResult contains the outcome of a content verification
type VerificationResult struct {
	ContentHash     ContentHash
	VerifiedBy      []NodeID
	Timestamp       time.Time
	Level           int
	Score           float64
	Disputed        bool
	DisputeReasons  []string
	CrossReferences []ContentHash
}

// NodeID represents a unique identifier for a verification node
type NodeID string

// Node represents a verification node in the consensus network
type Node struct {
	ID            NodeID
	PublicKey     []byte
	Reputation    float64
	Weight        float64
	Specialties   []string
	LastSeen      time.Time
	TotalVerified int
}

// ConsensusNetwork manages the distributed verification process
type ConsensusNetwork struct {
	nodes             map[NodeID]*Node
	verifications     map[ContentHash]*VerificationResult
	contentReferences map[ContentHash][]ContentHash
	mu                sync.RWMutex
}

// NewConsensusNetwork creates a new consensus network
func NewConsensusNetwork() *ConsensusNetwork {
	return &ConsensusNetwork{
		nodes:             make(map[NodeID]*Node),
		verifications:     make(map[ContentHash]*VerificationResult),
		contentReferences: make(map[ContentHash][]ContentHash),
	}
}

// RegisterNode adds a new verification node to the network
func (cn *ConsensusNetwork) RegisterNode(node *Node) error {
	if node == nil {
		return errors.New("node cannot be nil")
	}
	
	cn.mu.Lock()
	defer cn.mu.Unlock()
	
	if _, exists := cn.nodes[node.ID]; exists {
		return errors.New("node with this ID already exists")
	}
	
	node.LastSeen = time.Now()
	cn.nodes[node.ID] = node
	return nil
}

// SubmitVerification submits a verification for content
func (cn *ConsensusNetwork) SubmitVerification(
	nodeID NodeID,
	contentHash ContentHash,
	level int,
	crossRefs []ContentHash,
	disputed bool,
	disputeReasons []string,
) error {
	cn.mu.Lock()
	defer cn.mu.Unlock()
	
	// Check if node exists
	node, exists := cn.nodes[nodeID]
	if !exists {
		return errors.New("node not registered")
	}
	
	// Update node's last seen time
	node.LastSeen = time.Now()
	node.TotalVerified++
	
	// Check if content already has verification
	result, exists := cn.verifications[contentHash]
	if !exists {
		// Create new verification result
		result = &VerificationResult{
			ContentHash:     contentHash,
			VerifiedBy:      []NodeID{nodeID},
			Timestamp:       time.Now(),
			Level:           level,
			Score:           node.Weight * float64(level),
			Disputed:        disputed,
			DisputeReasons:  disputeReasons,
			CrossReferences: crossRefs,
		}
		cn.verifications[contentHash] = result
	} else {
		// Check if node already verified this content
		for _, id := range result.VerifiedBy {
			if id == nodeID {
				return errors.New("node already verified this content")
			}
		}
		
		// Update existing verification
		result.VerifiedBy = append(result.VerifiedBy, nodeID)
		result.Score += node.Weight * float64(level)
		
		// Update disputed status if necessary
		if disputed && !result.Disputed {
			result.Disputed = true
			result.DisputeReasons = disputeReasons
		} else if disputed {
			// Append new dispute reasons
			for _, reason := range disputeReasons {
				// Check if reason already exists
				exists := false
				for _, existingReason := range result.DisputeReasons {
					if existingReason == reason {
						exists = true
						break
					}
				}
				
				if !exists {
					result.DisputeReasons = append(result.DisputeReasons, reason)
				}
			}
		}
		
		// Update cross-references
		for _, ref := range crossRefs {
			exists := false
			for _, existingRef := range result.CrossReferences {
				if existingRef == ref {
					exists = true
					break
				}
			}
			
			if !exists {
				result.CrossReferences = append(result.CrossReferences, ref)
			}
		}
	}
	
	// Update content references
	cn.contentReferences[contentHash] = crossRefs
	
	return nil
}

// GetVerification retrieves the verification result for content
func (cn *ConsensusNetwork) GetVerification(contentHash ContentHash) (*VerificationResult, error) {
	cn.mu.RLock()
	defer cn.mu.RUnlock()
	
	result, exists := cn.verifications[contentHash]
	if !exists {
		return nil, errors.New("content has not been verified")
	}
	
	return result, nil
}

// GetVerificationLevel returns the overall verification level for content
func (cn *ConsensusNetwork) GetVerificationLevel(contentHash ContentHash) (int, error) {
	result, err := cn.GetVerification(contentHash)
	if err != nil {
		return VerificationLevelNone, err
	}
	
	// If content is disputed, cap the verification level
	if result.Disputed {
		return min(result.Level, VerificationLevelMinimal), nil
	}
	
	return result.Level, nil
}

// GetRelatedContent returns content related to the given content hash
func (cn *ConsensusNetwork) GetRelatedContent(contentHash ContentHash) ([]ContentHash, error) {
	cn.mu.RLock()
	defer cn.mu.RUnlock()
	
	refs, exists := cn.contentReferences[contentHash]
	if !exists {
		return nil, errors.New("content not found or has no references")
	}
	
	return refs, nil
}

// IsContentVerified checks if content has been verified
func (cn *ConsensusNetwork) IsContentVerified(contentHash ContentHash) bool {
	cn.mu.RLock()
	defer cn.mu.RUnlock()
	
	_, exists := cn.verifications[contentHash]
	return exists
}

// GetTrustScore calculates a trust score for content based on verifications
func (cn *ConsensusNetwork) GetTrustScore(contentHash ContentHash) (float64, error) {
	result, err := cn.GetVerification(contentHash)
	if err != nil {
		return 0.0, err
	}
	
	// Calculate trust score based on verification score and other factors
	trustScore := result.Score
	
	// Adjust for disputes
	if result.Disputed {
		trustScore *= 0.5 // Reduce score by half if disputed
	}
	
	// Adjust for number of verifiers
	verifierCount := len(result.VerifiedBy)
	if verifierCount > 1 {
		// Bonus for multiple verifiers
		trustScore *= (1.0 + float64(verifierCount-1)*0.1)
	}
	
	// Normalize to 0-1 range
	trustScore = min(1.0, max(0.0, trustScore/10.0))
	
	return trustScore, nil
}

// Helper functions
func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}

func max(a, b float64) float64 {
	if a > b {
		return a
	}
	return b
}
