package identity

import (
	"bytes"
	"testing"
)

// TestQZKPProviderInitClose tests that the QZKP provider can be initialized and closed
func TestQZKPProviderInitClose(t *testing.T) {
	provider, err := NewQZKPProvider()
	if err != nil {
		t.Fatalf("Failed to initialize QZKP provider: %v", err)
	}
	defer provider.Close()

	if !provider.initialized {
		t.Error("QZKP provider should be initialized")
	}

	provider.Close()
	if provider.initialized {
		t.Error("QZKP provider should not be initialized after close")
	}
}

// TestGeolocationCommitment tests creating a geolocation commitment
func TestGeolocationCommitment(t *testing.T) {
	provider, err := NewQZKPProvider()
	if err != nil {
		t.Fatalf("Failed to initialize QZKP provider: %v", err)
	}
	defer provider.Close()

	// Test parameters
	latitude := 37.7749
	longitude := -122.4194
	countryCode := "US"
	regionCode := "CA"

	// Generate commitment
	commitment, err := provider.CreateGeolocationCommitment(
		latitude, longitude, countryCode, regionCode,
	)
	if err != nil {
		t.Fatalf("Failed to create geolocation commitment: %v", err)
	}

	// Verify commitment is not empty
	if len(commitment) == 0 {
		t.Error("Geolocation commitment should not be empty")
	}

	// Generate another commitment with same parameters, should be deterministic
	commitment2, err := provider.CreateGeolocationCommitment(
		latitude, longitude, countryCode, regionCode,
	)
	if err != nil {
		t.Fatalf("Failed to create second geolocation commitment: %v", err)
	}

	// Commitments should be the same (deterministic)
	if !bytes.Equal(commitment, commitment2) {
		t.Error("Geolocation commitments should be deterministic for same input")
	}

	// Generate another commitment with different parameters
	commitment3, err := provider.CreateGeolocationCommitment(
		latitude+1.0, longitude, countryCode, regionCode,
	)
	if err != nil {
		t.Fatalf("Failed to create third geolocation commitment: %v", err)
	}

	// Commitments should be different
	if bytes.Equal(commitment, commitment3) {
		t.Error("Geolocation commitments should be different for different input")
	}
}

// TestZKProofGeneration tests generating and verifying zero-knowledge proofs
func TestZKProofGeneration(t *testing.T) {
	provider, err := NewQZKPProvider()
	if err != nil {
		t.Fatalf("Failed to initialize QZKP provider: %v", err)
	}
	defer provider.Close()

	// Test parameters
	secret := []byte("this is a secret value")
	publicInput := []byte("this is public information")

	// Generate proof
	proof, err := provider.GenerateZKProof(secret, publicInput)
	if err != nil {
		t.Fatalf("Failed to generate ZK proof: %v", err)
	}

	// Verify proof is not empty
	if len(proof) == 0 {
		t.Error("ZK proof should not be empty")
	}

	// Verify proof with correct public input
	valid, err := provider.VerifyZKProof(proof, publicInput)
	if err != nil {
		t.Fatalf("Failed to verify ZK proof: %v", err)
	}

	// The proof should be valid with the correct input
	if !valid {
		t.Error("ZK proof should be valid with correct public input")
	}

	// Verify proof with incorrect public input
	wrongInput := []byte("this is the wrong public information")
	valid, err = provider.VerifyZKProof(proof, wrongInput)
	if err != nil {
		t.Fatalf("Failed to verify ZK proof with wrong input: %v", err)
	}

	// The proof should be invalid with incorrect input
	if valid {
		t.Error("ZK proof should be invalid with incorrect public input")
	}
}

// TestCryptoAdapterInitClose tests that the crypto adapter can be initialized and closed
func TestCryptoAdapterInitClose(t *testing.T) {
	adapter, err := NewCryptoAdapter(true, true)
	if err != nil {
		t.Fatalf("Failed to initialize crypto adapter: %v", err)
	}
	defer adapter.Close()

	if !adapter.initialized {
		t.Error("Crypto adapter should be initialized")
	}

	adapter.Close()
	if adapter.initialized {
		t.Error("Crypto adapter should not be initialized after close")
	}
}

// TestKyberKeyGeneration tests generating Kyber key pairs
func TestKyberKeyGeneration(t *testing.T) {
	adapter, err := NewCryptoAdapter(true, true)
	if err != nil {
		t.Fatalf("Failed to initialize crypto adapter: %v", err)
	}
	defer adapter.Close()

	// Generate Kyber key pair
	publicKey, privateKey, err := adapter.GenerateKyberKey()
	if err != nil {
		t.Fatalf("Failed to generate Kyber key: %v", err)
	}

	// Verify keys are not empty
	if len(publicKey) == 0 || len(privateKey) == 0 {
		t.Error("Kyber keys should not be empty")
	}
}

// TestFalconKeyGeneration tests generating Falcon key pairs
func TestFalconKeyGeneration(t *testing.T) {
	adapter, err := NewCryptoAdapter(true, true)
	if err != nil {
		t.Fatalf("Failed to initialize crypto adapter: %v", err)
	}
	defer adapter.Close()

	// Generate Falcon key pair
	publicKey, privateKey, err := adapter.GenerateFalconKey()
	if err != nil {
		t.Fatalf("Failed to generate Falcon key: %v", err)
	}

	// Verify keys are not empty
	if len(publicKey) == 0 || len(privateKey) == 0 {
		t.Error("Falcon keys should not be empty")
	}
}

// TestMessageSigning tests signing and verifying messages with Falcon
func TestMessageSigning(t *testing.T) {
	adapter, err := NewCryptoAdapter(true, true)
	if err != nil {
		t.Fatalf("Failed to initialize crypto adapter: %v", err)
	}
	defer adapter.Close()

	// Generate Falcon key pair
	publicKey, privateKey, err := adapter.GenerateFalconKey()
	if err != nil {
		t.Fatalf("Failed to generate Falcon key: %v", err)
	}

	// Test message
	message := []byte("This is a test message for the crypto adapter")

	// Sign the message
	signature, err := adapter.SignMessage(message, privateKey)
	if err != nil {
		t.Fatalf("Failed to sign message: %v", err)
	}

	// Verify signature is not empty
	if len(signature) == 0 {
		t.Error("Signature should not be empty")
	}

	// Verify the signature with correct message
	valid, err := adapter.VerifySignature(message, signature, publicKey)
	if err != nil {
		t.Fatalf("Failed to verify signature: %v", err)
	}

	// The signature should be valid
	if !valid {
		t.Error("Signature should be valid with correct message")
	}

	// Verify with incorrect message
	wrongMessage := []byte("This is NOT the test message that was signed")
	valid, err = adapter.VerifySignature(wrongMessage, signature, publicKey)
	if err != nil {
		t.Fatalf("Failed to verify signature with wrong message: %v", err)
	}

	// The signature should be invalid with incorrect message
	if valid {
		t.Error("Signature should be invalid with incorrect message")
	}
}

// TestKeyExchange tests key exchange with Kyber
func TestKeyExchange(t *testing.T) {
	adapter, err := NewCryptoAdapter(true, true)
	if err != nil {
		t.Fatalf("Failed to initialize crypto adapter: %v", err)
	}
	defer adapter.Close()

	// Generate Kyber key pair for recipient
	recipientPublicKey, recipientPrivateKey, err := adapter.GenerateKyberKey()
	if err != nil {
		t.Fatalf("Failed to generate recipient Kyber key: %v", err)
	}

	// Sender establishes a shared key
	sharedSecret1, ciphertext, err := adapter.EstablishKey(recipientPublicKey)
	if err != nil {
		t.Fatalf("Failed to establish shared key: %v", err)
	}

	// Verify shared secret and ciphertext are not empty
	if len(sharedSecret1) == 0 || len(ciphertext) == 0 {
		t.Error("Shared secret and ciphertext should not be empty")
	}

	// Recipient decapsulates the shared key
	sharedSecret2, err := adapter.ReceiveKey(ciphertext, recipientPrivateKey)
	if err != nil {
		t.Fatalf("Failed to receive shared key: %v", err)
	}

	// Verify shared secret is not empty
	if len(sharedSecret2) == 0 {
		t.Error("Received shared secret should not be empty")
	}

	// Shared secrets should match
	if !bytes.Equal(sharedSecret1, sharedSecret2) {
		t.Error("Shared secrets should match between sender and recipient")
	}
}

// TestIntegrationWithZeroKnowledgeProvider tests the integration between QZKP and crypto adapter
func TestIntegrationWithZeroKnowledgeProvider(t *testing.T) {
	// Initialize QZKP provider
	qzkpProvider, err := NewQZKPProvider()
	if err != nil {
		t.Fatalf("Failed to initialize QZKP provider: %v", err)
	}
	defer qzkpProvider.Close()

	// Initialize crypto adapter
	cryptoAdapter, err := NewCryptoAdapter(true, true)
	if err != nil {
		t.Fatalf("Failed to initialize crypto adapter: %v", err)
	}
	defer cryptoAdapter.Close()

	// Generate Falcon key pair for signing
	publicKey, privateKey, err := cryptoAdapter.GenerateFalconKey()
	if err != nil {
		t.Fatalf("Failed to generate Falcon key: %v", err)
	}

	// Test parameters for geolocation commitment
	latitude := 37.7749
	longitude := -122.4194
	countryCode := "US"
	regionCode := "CA"

	// Generate geolocation commitment
	commitment, err := qzkpProvider.CreateGeolocationCommitment(
		latitude, longitude, countryCode, regionCode,
	)
	if err != nil {
		t.Fatalf("Failed to create geolocation commitment: %v", err)
	}

	// Sign the commitment with Falcon
	signature, err := cryptoAdapter.SignMessage(commitment, privateKey)
	if err != nil {
		t.Fatalf("Failed to sign commitment: %v", err)
	}

	// Verify the signature
	valid, err := cryptoAdapter.VerifySignature(commitment, signature, publicKey)
	if err != nil {
		t.Fatalf("Failed to verify signature: %v", err)
	}

	// The signature should be valid
	if !valid {
		t.Error("Signature on commitment should be valid")
	}
}
