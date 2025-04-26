// Package identity provides crypto integration for the core system
package identity

import (
	"fmt"
	"sync"
)

// CryptoProvider is the main interface to the Hydra cryptographic system
type CryptoProvider struct {
	hydra          *HydraCrypto
	keyCache       sync.Map
	sessionManager *SessionManager
}

// NewCryptoProvider creates a new crypto provider instance
func NewCryptoProvider() (*CryptoProvider, error) {
	hydra := NewHydraCrypto()
	
	// Initialize session manager
	sessionManager, err := NewSessionManager()
	if err != nil {
		return nil, fmt.Errorf("failed to initialize session manager: %v", err)
	}
	
	return &CryptoProvider{
		hydra:          hydra,
		sessionManager: sessionManager,
	}, nil
}

// CreateSourceVerification creates a source verification commitment
func (p *CryptoProvider) CreateSourceVerification(
	sourceID string,
	latitude, longitude float64,
	countryCode, regionCode string,
) ([]byte, error) {
	// Generate geolocation commitment
	commitment, err := p.hydra.CreateGeolocationCommitment(
		latitude, longitude, countryCode, regionCode,
	)
	if err != nil {
		return nil, fmt.Errorf("failed to create geolocation commitment: %v", err)
	}
	
	// Get the source's verification key
	keyPair, err := p.sessionManager.GetOrCreateSourceKeyPair(sourceID)
	if err != nil {
		return nil, fmt.Errorf("failed to get source key pair: %v", err)
	}
	
	// Sign the commitment with the source's key
	signature, err := p.hydra.SignMessage(commitment, keyPair.PrivateKey)
	if err != nil {
		return nil, fmt.Errorf("failed to sign commitment: %v", err)
	}
	
	// Combine commitment and signature for complete verification
	verification := make([]byte, len(commitment)+len(signature)+8)
	copy(verification[0:4], []byte{0x01, 0x02, 0x03, 0x04}) // Magic bytes
	copy(verification[4:4+len(commitment)], commitment)
	
	// Store signature length as 4 bytes
	sigLen := uint32(len(signature))
	verification[4+len(commitment)] = byte(sigLen & 0xFF)
	verification[4+len(commitment)+1] = byte((sigLen >> 8) & 0xFF)
	verification[4+len(commitment)+2] = byte((sigLen >> 16) & 0xFF)
	verification[4+len(commitment)+3] = byte((sigLen >> 24) & 0xFF)
	
	// Copy signature
	copy(verification[4+len(commitment)+4:], signature)
	
	return verification, nil
}

// VerifySourceLocation verifies a source's location claim
func (p *CryptoProvider) VerifySourceLocation(
	sourceID string,
	verificationData []byte,
	latitude, longitude float64,
	countryCode, regionCode string,
) (bool, error) {
	// Verify data format
	if len(verificationData) < 8 || 
		verificationData[0] != 0x01 || 
		verificationData[1] != 0x02 ||
		verificationData[2] != 0x03 ||
		verificationData[3] != 0x04 {
		return false, fmt.Errorf("invalid verification data format")
	}
	
	// Calculate expected commitment
	expectedCommitment, err := p.hydra.CreateGeolocationCommitment(
		latitude, longitude, countryCode, regionCode,
	)
	if err != nil {
		return false, fmt.Errorf("failed to create expected commitment: %v", err)
	}
	
	// Extract actual commitment
	commitmentLen := len(expectedCommitment)
	if len(verificationData) < 4+commitmentLen+4 {
		return false, fmt.Errorf("verification data too short")
	}
	
	actualCommitment := verificationData[4:4+commitmentLen]
	
	// Parse signature length
	sigLen := uint32(verificationData[4+commitmentLen]) |
		(uint32(verificationData[4+commitmentLen+1]) << 8) |
		(uint32(verificationData[4+commitmentLen+2]) << 16) |
		(uint32(verificationData[4+commitmentLen+3]) << 24)
	
	// Verify total length
	if len(verificationData) != 4+commitmentLen+4+int(sigLen) {
		return false, fmt.Errorf("invalid verification data length")
	}
	
	// Extract signature
	signature := verificationData[4+commitmentLen+4 : 4+commitmentLen+4+int(sigLen)]
	
	// Get source public key
	keyPair, err := p.sessionManager.GetOrCreateSourceKeyPair(sourceID)
	if err != nil {
		return false, fmt.Errorf("failed to get source key pair: %v", err)
	}
	
	// Verify signature
	valid, err := p.hydra.VerifySignature(actualCommitment, signature, keyPair.PublicKey)
	if err != nil {
		return false, fmt.Errorf("signature verification error: %v", err)
	}
	
	return valid, nil
}

// CreateContentEntanglement creates a logical entanglement for content verification
func (p *CryptoProvider) CreateContentEntanglement(
	title, content, author string,
	metadata map[string]string,
) ([]byte, error) {
	// Convert metadata to byte slices
	metadataBytes := make([]byte, 0)
	for k, v := range metadata {
		metadataBytes = append(metadataBytes, []byte(k+"="+v)...)
		metadataBytes = append(metadataBytes, byte(0)) // Null separator
	}
	
	// Create data items array
	dataItems := [][]byte{
		[]byte(title),
		[]byte(content),
		[]byte(author),
		metadataBytes,
	}
	
	// Create entanglement
	entanglement, err := p.hydra.CreateEntanglement(dataItems)
	if err != nil {
		return nil, fmt.Errorf("failed to create content entanglement: %v", err)
	}
	
	return entanglement, nil
}

// VerifyContentEntanglement verifies content against an entanglement hash
func (p *CryptoProvider) VerifyContentEntanglement(
	entanglement []byte,
	title, content, author string,
	metadata map[string]string,
) (bool, error) {
	// Convert metadata to byte slices (same as in CreateContentEntanglement)
	metadataBytes := make([]byte, 0)
	for k, v := range metadata {
		metadataBytes = append(metadataBytes, []byte(k+"="+v)...)
		metadataBytes = append(metadataBytes, byte(0)) // Null separator
	}
	
	// Create data items array
	dataItems := [][]byte{
		[]byte(title),
		[]byte(content),
		[]byte(author),
		metadataBytes,
	}
	
	// Verify entanglement
	valid, err := p.hydra.VerifyEntanglement(dataItems, entanglement)
	if err != nil {
		return false, fmt.Errorf("failed to verify content entanglement: %v", err)
	}
	
	return valid, nil
}

// EstablishSecureChannel establishes a secure communication channel
func (p *CryptoProvider) EstablishSecureChannel(
	receiverID string,
) (channelID string, sessionKey []byte, err error) {
	// Get receiver's key pair
	receiverKeyPair, err := p.sessionManager.GetOrCreateNodeKeyPair(receiverID)
	if err != nil {
		return "", nil, fmt.Errorf("failed to get receiver key pair: %v", err)
	}
	
	// Generate shared key
	sharedSecret, ciphertext, err := p.hydra.EstablishSharedKey(receiverKeyPair.PublicKey)
	if err != nil {
		return "", nil, fmt.Errorf("failed to establish shared key: %v", err)
	}
	
	// Create channel ID from ciphertext (first 16 bytes as hex)
	channelID = fmt.Sprintf("%x", ciphertext[:16])
	
	// Store channel information
	err = p.sessionManager.StoreChannel(channelID, receiverID, ciphertext)
	if err != nil {
		return "", nil, fmt.Errorf("failed to store channel: %v", err)
	}
	
	return channelID, sharedSecret, nil
}

// JoinSecureChannel joins an established secure channel
func (p *CryptoProvider) JoinSecureChannel(
	channelID string,
) (sessionKey []byte, err error) {
	// Get channel information
	receiverID, ciphertext, err := p.sessionManager.GetChannel(channelID)
	if err != nil {
		return nil, fmt.Errorf("failed to get channel: %v", err)
	}
	
	// Get receiver's key pair
	receiverKeyPair, err := p.sessionManager.GetOrCreateNodeKeyPair(receiverID)
	if err != nil {
		return nil, fmt.Errorf("failed to get receiver key pair: %v", err)
	}
	
	// Derive shared key
	sharedSecret, err := p.hydra.ReceiveSharedKey(ciphertext, receiverKeyPair.PrivateKey)
	if err != nil {
		return nil, fmt.Errorf("failed to receive shared key: %v", err)
	}
	
	return sharedSecret, nil
}
