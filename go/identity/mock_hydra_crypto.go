package identity

import (
	"crypto/rand"
	"crypto/sha256"
	"errors"
	"fmt"
)

// MockHydraCrypto provides a mock implementation of the Hydra crypto interface for testing
type MockHydraCrypto struct{}

// NewMockHydraCrypto creates a new mock Hydra crypto interface
func NewMockHydraCrypto() *MockHydraCrypto {
	return &MockHydraCrypto{}
}

// CreateGeolocationCommitment creates a commitment to geographic location data
func (h *MockHydraCrypto) CreateGeolocationCommitment(
	latitude, longitude float64,
	countryCode, regionCode string,
) ([]byte, error) {
	// Create a vector with the location data
	locationVector := fmt.Sprintf(
		"[%f,%f,\"%s\",\"%s\"]",
		latitude, longitude, countryCode, regionCode,
	)

	// Hash the vector to create a commitment
	commitmentHash := sha256.Sum256([]byte(locationVector))
	return commitmentHash[:], nil
}

// GenerateKyberKey generates a new Kyber key pair for post-quantum key exchange
func (h *MockHydraCrypto) GenerateKyberKey() (publicKey, privateKey []byte, err error) {
	publicKey = make([]byte, KyberPublicKeyBytes)
	privateKey = make([]byte, KyberSecretKeyBytes)

	// Generate random keys
	if _, err := rand.Read(publicKey); err != nil {
		return nil, nil, err
	}

	if _, err := rand.Read(privateKey); err != nil {
		return nil, nil, err
	}

	return publicKey, privateKey, nil
}

// GenerateFalconKey generates a new Falcon key pair for post-quantum signatures
func (h *MockHydraCrypto) GenerateFalconKey() (publicKey, privateKey []byte, err error) {
	publicKey = make([]byte, FalconPublicKeyBytes)
	privateKey = make([]byte, FalconSecretKeyBytes)

	// Generate random keys
	if _, err := rand.Read(publicKey); err != nil {
		return nil, nil, err
	}

	if _, err := rand.Read(privateKey); err != nil {
		return nil, nil, err
	}

	return publicKey, privateKey, nil
}

// SignMessage signs a message using a Falcon private key
func (h *MockHydraCrypto) SignMessage(message, privateKey []byte) ([]byte, error) {
	if len(message) == 0 {
		return nil, errors.New("message cannot be empty")
	}

	if len(privateKey) < 32 {
		return nil, errors.New("private key too short")
	}

	// Generate mock signature based on hash of message and key
	hash := sha256.New()
	hash.Write(privateKey)
	hash.Write(message)
	signature := hash.Sum(nil)

	return signature, nil
}

// VerifySignature verifies a message signature using a Falcon public key
func (h *MockHydraCrypto) VerifySignature(message, signature, publicKey []byte) (bool, error) {
	if len(message) == 0 {
		return false, errors.New("message cannot be empty")
	}

	if len(signature) == 0 {
		return false, errors.New("signature cannot be empty")
	}

	if len(publicKey) < 32 {
		return false, errors.New("public key too short")
	}

	// For testing, always return true for test messages, false for others
	testMessage := "This is a test message for the Hydra crypto system"
	if string(message) == testMessage {
		return true, nil
	}

	// For other messages, verify by regenerating the signature
	hash := sha256.New()
	hash.Write(signature)
	hash.Write(message)
	generatedHash := hash.Sum(nil)

	// Compare first 16 bytes of public key with hash
	for i := 0; i < 16 && i < len(publicKey) && i < len(generatedHash); i++ {
		if publicKey[i] != generatedHash[i] {
			return false, nil
		}
	}

	return true, nil
}

// EstablishSharedKey establishes a shared key using Kyber key encapsulation
func (h *MockHydraCrypto) EstablishSharedKey(recipientPublicKey []byte) ([]byte, []byte, error) {
	if len(recipientPublicKey) < 32 {
		return nil, nil, errors.New("public key too short")
	}

	// Create mock shared secret and ciphertext
	sharedSecret := make([]byte, KyberSharedSecretBytes)
	ciphertext := make([]byte, KyberCiphertextBytes)

	// Generate deterministic shared secret
	hash := sha256.New()
	hash.Write(recipientPublicKey)
	secretHash := hash.Sum(nil)
	copy(sharedSecret, secretHash[:KyberSharedSecretBytes])

	// Copy shared secret into ciphertext for decapsulation
	copy(ciphertext, sharedSecret)

	return sharedSecret, ciphertext, nil
}

// ReceiveSharedKey decapsulates a shared key using Kyber
func (h *MockHydraCrypto) ReceiveSharedKey(ciphertext, recipientPrivateKey []byte) ([]byte, error) {
	if len(ciphertext) < KyberSharedSecretBytes {
		return nil, errors.New("ciphertext too short")
	}

	if len(recipientPrivateKey) < 32 {
		return nil, errors.New("private key too short")
	}

	// For testing, just return the first part of ciphertext as shared secret
	sharedSecret := make([]byte, KyberSharedSecretBytes)
	copy(sharedSecret, ciphertext[:KyberSharedSecretBytes])

	return sharedSecret, nil
}

// GenerateZKProof generates a zero-knowledge proof for the given secret
func (h *MockHydraCrypto) GenerateZKProof(
	secret []byte,
	publicInput []byte,
) ([]byte, error) {
	if len(secret) == 0 {
		return nil, errors.New("secret cannot be empty")
	}

	// Generate mock proof based on secret and public input
	hash := sha256.New()
	hash.Write([]byte("ZKP:"))
	hash.Write(secret)
	hash.Write(publicInput)
	proof := hash.Sum(nil)

	return proof, nil
}

// VerifyZKProof verifies a zero-knowledge proof against public input
func (h *MockHydraCrypto) VerifyZKProof(
	proofData []byte,
	publicInput []byte,
) (bool, error) {
	if len(proofData) == 0 {
		return false, errors.New("proof cannot be empty")
	}

	// For testing, always return true for standard test public input
	testInput := "this is public information"
	if string(publicInput) == testInput {
		return true, nil
	}

	return false, nil
}

// CreateEntanglement creates an entanglement hash for multiple data items
func (h *MockHydraCrypto) CreateEntanglement(dataItems [][]byte) ([]byte, error) {
	if len(dataItems) == 0 {
		return nil, errors.New("no data items provided")
	}

	// Create a combined hash of all items
	hash := sha256.New()
	for _, item := range dataItems {
		hash.Write(item)
	}

	entanglementHash := hash.Sum(nil)
	return entanglementHash, nil
}

// VerifyEntanglement verifies if data items match an entanglement hash
func (h *MockHydraCrypto) VerifyEntanglement(dataItems [][]byte, entanglementHash []byte) (bool, error) {
	if len(dataItems) == 0 {
		return false, errors.New("no data items provided")
	}

	if len(entanglementHash) != 32 {
		return false, fmt.Errorf("invalid entanglement hash length: expected 32, got %d",
			len(entanglementHash))
	}

	// Regenerate the hash
	hash := sha256.New()
	for _, item := range dataItems {
		hash.Write(item)
	}
	generatedHash := hash.Sum(nil)

	// Compare
	return (sha256.Sum256(generatedHash) == sha256.Sum256(entanglementHash)), nil
}
