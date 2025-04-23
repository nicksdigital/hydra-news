// Package consensus implements Byzantine Fault Tolerance for Hydra News
package consensus

import (
	"crypto/ed25519"
	"crypto/rand"
	"crypto/sha256"
	"encoding/base64"
	"encoding/json"
	"errors"
	"fmt"
	"sync"
	"time"
)

// MessageType represents different message types in the BFT protocol
type MessageType int

const (
	MessageTypePrepare MessageType = iota
	MessageTypeCommit
	MessageTypeViewChange
	MessageTypeNewView
)

// ConsensusState represents the current state of the consensus
type ConsensusState int

const (
	ConsensusStateNormal ConsensusState = iota
	ConsensusStateViewChange
	ConsensusStateNewView
)

// Message represents a consensus message in the BFT protocol
type Message struct {
	Type         MessageType
	NodeID       NodeID
	View         int
	Sequence     int
	ContentHash  ContentHash
	Digest       []byte
	Timestamp    time.Time
	Signature    []byte
	PrepareCount int
	CommitCount  int
}

// ConsensusResult represents the outcome of a consensus round
type ConsensusResult struct {
	ContentHash ContentHash
	Consensus   bool
	Signers     []NodeID
	Timestamp   time.Time
}

// BFTConsensus implements Byzantine Fault Tolerance for news content verification
type BFTConsensus struct {
	nodeID          NodeID
	privateKey      ed25519.PrivateKey
	publicKey       ed25519.PublicKey
	nodes           map[NodeID]ed25519.PublicKey
	view            int
	sequence        int
	prepareMessages map[string]map[NodeID]*Message
	commitMessages  map[string]map[NodeID]*Message
	results         map[string]*ConsensusResult
	state           ConsensusState
	f               int // Maximum number of faulty nodes tolerated
	mu              sync.RWMutex
}

// NewBFTConsensus creates a new BFT consensus instance
func NewBFTConsensus(nodeID NodeID, f int) (*BFTConsensus, error) {
	// Generate new key pair
	publicKey, privateKey, err := ed25519.GenerateKey(rand.Reader)
	if err != nil {
		return nil, fmt.Errorf("failed to generate key pair: %v", err)
	}
	
	return &BFTConsensus{
		nodeID:          nodeID,
		privateKey:      privateKey,
		publicKey:       publicKey,
		nodes:           make(map[NodeID]ed25519.PublicKey),
		view:            0,
		sequence:        0,
		prepareMessages: make(map[string]map[NodeID]*Message),
		commitMessages:  make(map[string]map[NodeID]*Message),
		results:         make(map[string]*ConsensusResult),
		state:           ConsensusStateNormal,
		f:               f,
	}, nil
}

// RegisterNode adds a node to the consensus network
func (bft *BFTConsensus) RegisterNode(nodeID NodeID, publicKey ed25519.PublicKey) error {
	bft.mu.Lock()
	defer bft.mu.Unlock()
	
	if _, exists := bft.nodes[nodeID]; exists {
		return errors.New("node already registered")
	}
	
	bft.nodes[nodeID] = publicKey
	return nil
}

// ProposeContent initiates consensus for content verification
func (bft *BFTConsensus) ProposeContent(content []byte) (*ConsensusResult, error) {
	bft.mu.Lock()
	defer bft.mu.Unlock()
	
	if bft.state != ConsensusStateNormal {
		return nil, errors.New("consensus is not in normal state")
	}
	
	// Hash the content
	contentHash := sha256.Sum256(content)
	
	// Create message digest
	digest := sha256.Sum256(append(contentHash[:], byte(bft.view), byte(bft.sequence)))
	
	// Create prepare message
	prepareMsg := &Message{
		Type:        MessageTypePrepare,
		NodeID:      bft.nodeID,
		View:        bft.view,
		Sequence:    bft.sequence,
		ContentHash: contentHash,
		Digest:      digest[:],
		Timestamp:   time.Now(),
	}
	
	// Sign the message
	prepareMsg.Signature = bft.signMessage(prepareMsg)
	
	// Initialize message maps if needed
	contentKey := contentHash.String()
	if _, exists := bft.prepareMessages[contentKey]; !exists {
		bft.prepareMessages[contentKey] = make(map[NodeID]*Message)
	}
	if _, exists := bft.commitMessages[contentKey]; !exists {
		bft.commitMessages[contentKey] = make(map[NodeID]*Message)
	}
	
	// Add own prepare message
	bft.prepareMessages[contentKey][bft.nodeID] = prepareMsg
	
	// Broadcast prepare message to other nodes
	// In a real implementation, this would use network communication
	
	// Increment sequence number
	bft.sequence++
	
	// Create and return a pending result
	result := &ConsensusResult{
		ContentHash: contentHash,
		Consensus:   false,
		Signers:     []NodeID{bft.nodeID},
		Timestamp:   time.Now(),
	}
	
	bft.results[contentKey] = result
	
	return result, nil
}

// ProcessMessage processes a consensus message from another node
func (bft *BFTConsensus) ProcessMessage(msg *Message) error {
	if msg == nil {
		return errors.New("message cannot be nil")
	}
	
	// Verify signature
	if !bft.verifySignature(msg) {
		return errors.New("invalid message signature")
	}
	
	bft.mu.Lock()
	defer bft.mu.Unlock()
	
	// Process based on message type
	switch msg.Type {
	case MessageTypePrepare:
		return bft.processPrepareMessage(msg)
	case MessageTypeCommit:
		return bft.processCommitMessage(msg)
	case MessageTypeViewChange:
		return bft.processViewChangeMessage(msg)
	case MessageTypeNewView:
		return bft.processNewViewMessage(msg)
	default:
		return fmt.Errorf("unknown message type: %d", msg.Type)
	}
}

// Process a PREPARE message
func (bft *BFTConsensus) processPrepareMessage(msg *Message) error {
	if bft.state != ConsensusStateNormal {
		return errors.New("not in normal state")
	}
	
	contentKey := msg.ContentHash.String()
	
	// Initialize message maps if needed
	if _, exists := bft.prepareMessages[contentKey]; !exists {
		bft.prepareMessages[contentKey] = make(map[NodeID]*Message)
	}
	if _, exists := bft.commitMessages[contentKey]; !exists {
		bft.commitMessages[contentKey] = make(map[NodeID]*Message)
	}
	
	// Store prepare message
	bft.prepareMessages[contentKey][msg.NodeID] = msg
	
	// Check if we have enough prepare messages
	prepareCount := len(bft.prepareMessages[contentKey])
	
	// We need 2f+1 prepare messages to move to commit phase
	if prepareCount >= 2*bft.f+1 {
		// Create commit message
		commitMsg := &Message{
			Type:         MessageTypeCommit,
			NodeID:       bft.nodeID,
			View:         bft.view,
			Sequence:     msg.Sequence,
			ContentHash:  msg.ContentHash,
			Digest:       msg.Digest,
			Timestamp:    time.Now(),
			PrepareCount: prepareCount,
		}
		
		// Sign commit message
		commitMsg.Signature = bft.signMessage(commitMsg)
		
		// Store own commit message
		bft.commitMessages[contentKey][bft.nodeID] = commitMsg
		
		// Broadcast commit message
		// In a real implementation, this would use network communication
	}
	
	return nil
}

// Process a COMMIT message
func (bft *BFTConsensus) processCommitMessage(msg *Message) error {
	if bft.state != ConsensusStateNormal {
		return errors.New("not in normal state")
	}
	
	contentKey := msg.ContentHash.String()
	
	// Initialize message maps if needed
	if _, exists := bft.commitMessages[contentKey]; !exists {
		bft.commitMessages[contentKey] = make(map[NodeID]*Message)
	}
	
	// Store commit message
	bft.commitMessages[contentKey][msg.NodeID] = msg
	
	// Check if we have enough commit messages for consensus
	commitCount := len(bft.commitMessages[contentKey])
	
	// We need 2f+1 commit messages for consensus
	if commitCount >= 2*bft.f+1 {
		// Create list of signers
		signers := make([]NodeID, 0, commitCount)
		for nodeID := range bft.commitMessages[contentKey] {
			signers = append(signers, nodeID)
		}
		
		// Create or update consensus result
		result := &ConsensusResult{
			ContentHash: msg.ContentHash,
			Consensus:   true,
			Signers:     signers,
			Timestamp:   time.Now(),
		}
		
		bft.results[contentKey] = result
		
		// In a real implementation, notify application layer of consensus
	}
	
	return nil
}

// Process a VIEW-CHANGE message
func (bft *BFTConsensus) processViewChangeMessage(msg *Message) error {
	// Implementation of view change protocol
	// This is simplified - a real implementation would be more complex
	return nil
}

// Process a NEW-VIEW message
func (bft *BFTConsensus) processNewViewMessage(msg *Message) error {
	// Implementation of new view protocol
	// This is simplified - a real implementation would be more complex
	return nil
}

// GetConsensusResult retrieves the consensus result for content
func (bft *BFTConsensus) GetConsensusResult(contentHash ContentHash) (*ConsensusResult, error) {
	bft.mu.RLock()
	defer bft.mu.RUnlock()
	
	contentKey := contentHash.String()
	result, exists := bft.results[contentKey]
	if !exists {
		return nil, errors.New("no consensus result for content")
	}
	
	return result, nil
}

// Helper methods

// Sign a message using the node's private key
func (bft *BFTConsensus) signMessage(msg *Message) []byte {
	// Serialize message for signing (excluding signature field)
	msgBytes, _ := json.Marshal(struct {
		Type        MessageType
		NodeID      NodeID
		View        int
		Sequence    int
		ContentHash ContentHash
		Digest      []byte
		Timestamp   time.Time
	}{
		Type:        msg.Type,
		NodeID:      msg.NodeID,
		View:        msg.View,
		Sequence:    msg.Sequence,
		ContentHash: msg.ContentHash,
		Digest:      msg.Digest,
		Timestamp:   msg.Timestamp,
	})
	
	// Sign the message
	return ed25519.Sign(bft.privateKey, msgBytes)
}

// Verify a message signature
func (bft *BFTConsensus) verifySignature(msg *Message) bool {
	// Get the node's public key
	publicKey, exists := bft.nodes[msg.NodeID]
	if !exists {
		return false
	}
	
	// Serialize message for verification (excluding signature field)
	msgBytes, _ := json.Marshal(struct {
		Type        MessageType
		NodeID      NodeID
		View        int
		Sequence    int
		ContentHash ContentHash
		Digest      []byte
		Timestamp   time.Time
	}{
		Type:        msg.Type,
		NodeID:      msg.NodeID,
		View:        msg.View,
		Sequence:    msg.Sequence,
		ContentHash: msg.ContentHash,
		Digest:      msg.Digest,
		Timestamp:   msg.Timestamp,
	})
	
	// Verify the signature
	return ed25519.Verify(publicKey, msgBytes, msg.Signature)
}
