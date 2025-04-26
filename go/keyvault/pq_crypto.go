// Package keyvault provides cryptographic key management with post-quantum security
package keyvault

import (
	"crypto/rand"
	"encoding/hex"
	"errors"
	"fmt"
	"hydranews/identity"
	"time"
)

// PQCryptoManager manages post-quantum cryptographic operations
type PQCryptoManager struct {
	cryptoAdapter *identity.CryptoAdapter
	keys          map[string]*PQKeyInfo
}

// NewPQCryptoManager creates a new post-quantum crypto manager
func NewPQCryptoManager() (*PQCryptoManager, error) {
	// Initialize the crypto adapter with post-quantum and hybrid modes enabled
	adapter, err := identity.NewCryptoAdapter(true, true)
	if err != nil {
		return nil, fmt.Errorf("failed to initialize crypto adapter: %v", err)
	}

	return &PQCryptoManager{
		cryptoAdapter: adapter,
		keys:          make(map[string]*PQKeyInfo),
	}, nil
}

// Close releases resources used by the crypto manager
func (m *PQCryptoManager) Close() {
	if m.cryptoAdapter != nil {
		m.cryptoAdapter.Close()
		m.cryptoAdapter = nil
	}
	
	// Clear sensitive key data
	for _, key := range m.keys {
		if key.PrivateKey != nil {
			for i := range key.PrivateKey {
				key.PrivateKey[i] = 0
			}
		}
	}
}

// GenerateKyberKey generates a new Kyber key for key encapsulation
func (m *PQCryptoManager) GenerateKyberKey(purpose KeyPurpose, validityDays int) (*PQKeyInfo, error) {
	if m.cryptoAdapter == nil {
		return nil, errors.New("crypto manager is not initialized")
	}

	// Generate key using the C implementation
	publicKey, privateKey, err := m.cryptoAdapter.GenerateKyberKey()
	if err != nil {
		return nil, fmt.Errorf("failed to generate Kyber key: %v", err)
	}

	// Generate a random ID for the key
	idBytes := make([]byte, 16)
	if _, err := rand.Read(idBytes); err != nil {
		return nil, fmt.Errorf("failed to generate key ID: %v", err)
	}
	id := hex.EncodeToString(idBytes)

	// Calculate expiration time
	now := time.Now()
	expires := now.AddDate(0, 0, validityDays)

	// Create key info
	keyInfo := &PQKeyInfo{
		ID:         id,
		Type:       PQKeyTypeKyber,
		Purpose:    purpose,
		CreatedAt:  now,
		ExpiresAt:  expires,
		PublicKey:  publicKey,
		PrivateKey: privateKey,
	}

	// Store the key info
	m.keys[id] = keyInfo

	return keyInfo, nil
}

// GenerateFalconKey generates a new Falcon key for signatures
func (m *PQCryptoManager) GenerateFalconKey(purpose KeyPurpose, validityDays int) (*PQKeyInfo, error) {
	if m.cryptoAdapter == nil {
		return nil, errors.New("crypto manager is not initialized")
	}

	// Generate key using the C implementation
	publicKey, privateKey, err := m.cryptoAdapter.GenerateFalconKey()
	if err != nil {
		return nil, fmt.Errorf("failed to generate Falcon key: %v", err)
	}

	// Generate a random ID for the key
	idBytes := make([]byte, 16)
	if _, err := rand.Read(idBytes); err != nil {
		return nil, fmt.Errorf("failed to generate key ID: %v", err)
	}
	id := hex.EncodeToString(idBytes)

	// Calculate expiration time
	now := time.Now()
	expires := now.AddDate(0, 0, validityDays)

	// Create key info
	keyInfo := &PQKeyInfo{
		ID:         id,
		Type:       PQKeyTypeFalcon,
		Purpose:    purpose,
		CreatedAt:  now,
		ExpiresAt:  expires,
		PublicKey:  publicKey,
		PrivateKey: privateKey,
	}

	// Store the key info
	m.keys[id] = keyInfo

	return keyInfo, nil
}

// GetKey retrieves a key by ID
func (m *PQCryptoManager) GetKey(id string) (*PQKeyInfo, error) {
	key, exists := m.keys[id]
	if !exists {
		return nil, fmt.Errorf("key with ID %s not found", id)
	}

	// Check if key has expired
	if time.Now().After(key.ExpiresAt) {
		return nil, fmt.Errorf("key with ID %s has expired", id)
	}

	return key, nil
}

// DeleteKey securely deletes a key
func (m *PQCryptoManager) DeleteKey(id string) error {
	key, exists := m.keys[id]
	if !exists {
		return fmt.Errorf("key with ID %s not found", id)
	}

	// Securely clear private key data
	if key.PrivateKey != nil {
		for i := range key.PrivateKey {
			key.PrivateKey[i] = 0
		}
	}

	// Remove key from map
	delete(m.keys, id)

	return nil
}

// SignMessage signs a message using a Falcon private key
func (m *PQCryptoManager) SignMessage(message []byte, keyID string) ([]byte, error) {
	// Get the signing key
	signingKey, err := m.GetKey(keyID)
	if err != nil {
		return nil, fmt.Errorf("failed to get signing key: %v", err)
	}

	if signingKey.Type != PQKeyTypeFalcon {
		return nil, errors.New("signing key is not a Falcon key")
	}

	// Sign the message using the C implementation
	signature, err := m.cryptoAdapter.SignMessage(message, signingKey.PrivateKey)
	if err != nil {
		return nil, fmt.Errorf("failed to sign message: %v", err)
	}

	return signature, nil
}

// VerifySignature verifies a message signature using a Falcon public key
func (m *PQCryptoManager) VerifySignature(message, signature []byte, keyID string) (bool, error) {
	// Get the verification key
	verificationKey, err := m.GetKey(keyID)
	if err != nil {
		return false, fmt.Errorf("failed to get verification key: %v", err)
	}

	if verificationKey.Type != PQKeyTypeFalcon {
		return false, errors.New("verification key is not a Falcon key")
	}

	// Verify the signature using the C implementation
	valid, err := m.cryptoAdapter.VerifySignature(message, signature, verificationKey.PublicKey)
	if err != nil {
		return false, fmt.Errorf("failed to verify signature: %v", err)
	}

	return valid, nil
}

// EstablishSharedKey establishes a shared key using Kyber key encapsulation
func (m *PQCryptoManager) EstablishSharedKey(recipientKeyID string) ([]byte, []byte, error) {
	// Get recipient's public key
	recipientKey, err := m.GetKey(recipientKeyID)
	if err != nil {
		return nil, nil, fmt.Errorf("failed to get recipient key: %v", err)
	}

	if recipientKey.Type != PQKeyTypeKyber {
		return nil, nil, errors.New("recipient key is not a Kyber key")
	}

	// Establish shared key using the C implementation
	sharedSecret, ciphertext, err := m.cryptoAdapter.EstablishKey(recipientKey.PublicKey)
	if err != nil {
		return nil, nil, fmt.Errorf("failed to establish shared key: %v", err)
	}

	return sharedSecret, ciphertext, nil
}

// ReceiveSharedKey decapsulates a shared key using Kyber
func (m *PQCryptoManager) ReceiveSharedKey(recipientKeyID string, ciphertext []byte) ([]byte, error) {
	// Get recipient's private key
	recipientKey, err := m.GetKey(recipientKeyID)
	if err != nil {
		return nil, fmt.Errorf("failed to get recipient key: %v", err)
	}

	if recipientKey.Type != PQKeyTypeKyber {
		return nil, errors.New("recipient key is not a Kyber key")
	}

	// Receive shared key using the C implementation
	sharedSecret, err := m.cryptoAdapter.ReceiveKey(ciphertext, recipientKey.PrivateKey)
	if err != nil {
		return nil, fmt.Errorf("failed to receive shared key: %v", err)
	}

	return sharedSecret, nil
}
