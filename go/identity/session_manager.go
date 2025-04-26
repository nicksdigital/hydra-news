package identity

import (
	"crypto/rand"
	"encoding/hex"
	"fmt"
	"sync"
	"time"
)

// KeyPair represents a cryptographic key pair
type KeyPair struct {
	PublicKey  []byte
	PrivateKey []byte
	CreatedAt  time.Time
	ExpiresAt  time.Time
}

// Channel represents a secure communication channel
type Channel struct {
	ChannelID   string
	ReceiverID  string
	Ciphertext  []byte
	CreatedAt   time.Time
	ExpiresAt   time.Time
}

// SessionManager manages cryptographic sessions and keys
type SessionManager struct {
	hydra           *HydraCrypto
	sourceKeys      sync.Map // map[sourceID]KeyPair
	nodeKeys        sync.Map // map[nodeID]KeyPair
	channels        sync.Map // map[channelID]Channel
	keyExpiration   time.Duration
	channelTimeout  time.Duration
	mutex           sync.Mutex
}

// NewSessionManager creates a new session manager
func NewSessionManager() (*SessionManager, error) {
	return &SessionManager{
		hydra:           NewHydraCrypto(),
		keyExpiration:   24 * time.Hour,    // Keys expire after 24 hours
		channelTimeout:  30 * time.Minute,  // Channels timeout after 30 minutes
	}, nil
}

// GetOrCreateSourceKeyPair gets or creates a key pair for a source
func (m *SessionManager) GetOrCreateSourceKeyPair(sourceID string) (*KeyPair, error) {
	// Check if key already exists
	if val, ok := m.sourceKeys.Load(sourceID); ok {
		keyPair := val.(*KeyPair)
		
		// Check if key is expired
		if time.Now().Before(keyPair.ExpiresAt) {
			return keyPair, nil
		}
		
		// Key is expired, remove it
		m.sourceKeys.Delete(sourceID)
	}
	
	// Create new key pair
	m.mutex.Lock()
	defer m.mutex.Unlock()
	
	// Double-check if key was created while waiting for lock
	if val, ok := m.sourceKeys.Load(sourceID); ok {
		keyPair := val.(*KeyPair)
		if time.Now().Before(keyPair.ExpiresAt) {
			return keyPair, nil
		}
	}
	
	// Generate a new Falcon key pair
	publicKey, privateKey, err := m.hydra.GenerateFalconKey()
	if err != nil {
		return nil, fmt.Errorf("failed to generate Falcon key: %v", err)
	}
	
	// Create key pair
	keyPair := &KeyPair{
		PublicKey:  publicKey,
		PrivateKey: privateKey,
		CreatedAt:  time.Now(),
		ExpiresAt:  time.Now().Add(m.keyExpiration),
	}
	
	// Store key pair
	m.sourceKeys.Store(sourceID, keyPair)
	
	return keyPair, nil
}

// GetOrCreateNodeKeyPair gets or creates a Kyber key pair for a node
func (m *SessionManager) GetOrCreateNodeKeyPair(nodeID string) (*KeyPair, error) {
	// Check if key already exists
	if val, ok := m.nodeKeys.Load(nodeID); ok {
		keyPair := val.(*KeyPair)
		
		// Check if key is expired
		if time.Now().Before(keyPair.ExpiresAt) {
			return keyPair, nil
		}
		
		// Key is expired, remove it
		m.nodeKeys.Delete(nodeID)
	}
	
	// Create new key pair
	m.mutex.Lock()
	defer m.mutex.Unlock()
	
	// Double-check if key was created while waiting for lock
	if val, ok := m.nodeKeys.Load(nodeID); ok {
		keyPair := val.(*KeyPair)
		if time.Now().Before(keyPair.ExpiresAt) {
			return keyPair, nil
		}
	}
	
	// Generate a new Kyber key pair
	publicKey, privateKey, err := m.hydra.GenerateKyberKey()
	if err != nil {
		return nil, fmt.Errorf("failed to generate Kyber key: %v", err)
	}
	
	// Create key pair
	keyPair := &KeyPair{
		PublicKey:  publicKey,
		PrivateKey: privateKey,
		CreatedAt:  time.Now(),
		ExpiresAt:  time.Now().Add(m.keyExpiration),
	}
	
	// Store key pair
	m.nodeKeys.Store(nodeID, keyPair)
	
	return keyPair, nil
}

// StoreChannel stores a secure channel
func (m *SessionManager) StoreChannel(channelID, receiverID string, ciphertext []byte) error {
	// Create channel
	channel := &Channel{
		ChannelID:   channelID,
		ReceiverID:  receiverID,
		Ciphertext:  ciphertext,
		CreatedAt:   time.Now(),
		ExpiresAt:   time.Now().Add(m.channelTimeout),
	}
	
	// Store channel
	m.channels.Store(channelID, channel)
	
	return nil
}

// GetChannel gets a secure channel
func (m *SessionManager) GetChannel(channelID string) (receiverID string, ciphertext []byte, err error) {
	// Get channel
	val, ok := m.channels.Load(channelID)
	if !ok {
		return "", nil, fmt.Errorf("channel not found: %s", channelID)
	}
	
	channel := val.(*Channel)
	
	// Check if channel is expired
	if time.Now().After(channel.ExpiresAt) {
		m.channels.Delete(channelID)
		return "", nil, fmt.Errorf("channel expired: %s", channelID)
	}
	
	return channel.ReceiverID, channel.Ciphertext, nil
}

// GenerateRandomID generates a random ID for various uses
func (m *SessionManager) GenerateRandomID(prefix string, length int) (string, error) {
	// Generate random bytes
	bytes := make([]byte, length)
	_, err := rand.Read(bytes)
	if err != nil {
		return "", fmt.Errorf("failed to generate random bytes: %v", err)
	}
	
	// Convert to hex string
	id := prefix + hex.EncodeToString(bytes)
	
	return id, nil
}

// CleanupExpiredSessions removes expired sessions and keys
func (m *SessionManager) CleanupExpiredSessions() {
	now := time.Now()
	
	// Clean up source keys
	m.sourceKeys.Range(func(key, value interface{}) bool {
		keyPair := value.(*KeyPair)
		if now.After(keyPair.ExpiresAt) {
			m.sourceKeys.Delete(key)
		}
		return true
	})
	
	// Clean up node keys
	m.nodeKeys.Range(func(key, value interface{}) bool {
		keyPair := value.(*KeyPair)
		if now.After(keyPair.ExpiresAt) {
			m.nodeKeys.Delete(key)
		}
		return true
	})
	
	// Clean up channels
	m.channels.Range(func(key, value interface{}) bool {
		channel := value.(*Channel)
		if now.After(channel.ExpiresAt) {
			m.channels.Delete(key)
		}
		return true
	})
}

// StartCleanupService starts a background service to clean up expired sessions
func (m *SessionManager) StartCleanupService(interval time.Duration) {
	go func() {
		ticker := time.NewTicker(interval)
		defer ticker.Stop()
		
		for {
			<-ticker.C
			m.CleanupExpiredSessions()
		}
	}()
}
