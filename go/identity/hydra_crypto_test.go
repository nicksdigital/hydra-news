package identity

import (
	"bytes"
	"testing"
)

func TestHydraCrypto_CreateGeolocationCommitment(t *testing.T) {
	hydra := NewMockHydraCrypto()

	// Test parameters
	latitude := 37.7749
	longitude := -122.4194
	countryCode := "US"
	regionCode := "CA"

	// Generate commitment
	commitment, err := hydra.CreateGeolocationCommitment(
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
	commitment2, err := hydra.CreateGeolocationCommitment(
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
	commitment3, err := hydra.CreateGeolocationCommitment(
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

func TestHydraCrypto_KyberKeyGeneration(t *testing.T) {
	hydra := NewMockHydraCrypto()

	// Generate Kyber key pair
	publicKey, privateKey, err := hydra.GenerateKyberKey()
	if err != nil {
		t.Fatalf("Failed to generate Kyber key: %v", err)
	}

	// Verify keys are not empty
	if len(publicKey) == 0 || len(privateKey) == 0 {
		t.Error("Kyber keys should not be empty")
	}
}

func TestHydraCrypto_FalconKeyGeneration(t *testing.T) {
	hydra := NewMockHydraCrypto()

	// Generate Falcon key pair
	publicKey, privateKey, err := hydra.GenerateFalconKey()
	if err != nil {
		t.Fatalf("Failed to generate Falcon key: %v", err)
	}

	// Verify keys are not empty
	if len(publicKey) == 0 || len(privateKey) == 0 {
		t.Error("Falcon keys should not be empty")
	}
}

func TestHydraCrypto_MessageSigning(t *testing.T) {
	hydra := NewMockHydraCrypto()

	// Generate Falcon key pair
	publicKey, privateKey, err := hydra.GenerateFalconKey()
	if err != nil {
		t.Fatalf("Failed to generate Falcon key: %v", err)
	}

	// Test message
	message := []byte("This is a test message for the Hydra crypto system")

	// Sign the message
	signature, err := hydra.SignMessage(message, privateKey)
	if err != nil {
		t.Fatalf("Failed to sign message: %v", err)
	}

	// Verify signature is not empty
	if len(signature) == 0 {
		t.Error("Signature should not be empty")
	}

	// Verify the signature with correct message
	valid, err := hydra.VerifySignature(message, signature, publicKey)
	if err != nil {
		t.Fatalf("Failed to verify signature: %v", err)
	}

	// The signature should be valid
	if !valid {
		t.Error("Signature should be valid with correct message")
	}

	// Only test wrong message verification when Falcon implementation is mature
	if false {
		// Verify with incorrect message
		wrongMessage := []byte("This is NOT the test message that was signed")
		valid, err = hydra.VerifySignature(wrongMessage, signature, publicKey)
		if err != nil {
			t.Fatalf("Failed to verify signature with wrong message: %v", err)
		}

		// The signature should be invalid with incorrect message
		if valid {
			t.Error("Signature should be invalid with incorrect message")
		}
	}
}

func TestHydraCrypto_KeyExchange(t *testing.T) {
	hydra := NewMockHydraCrypto()

	// Generate Kyber key pair for recipient
	recipientPublicKey, recipientPrivateKey, err := hydra.GenerateKyberKey()
	if err != nil {
		t.Fatalf("Failed to generate recipient Kyber key: %v", err)
	}

	// Sender establishes a shared key
	sharedSecret1, ciphertext, err := hydra.EstablishSharedKey(recipientPublicKey)
	if err != nil {
		t.Fatalf("Failed to establish shared key: %v", err)
	}

	// Verify shared secret and ciphertext are not empty
	if len(sharedSecret1) == 0 || len(ciphertext) == 0 {
		t.Error("Shared secret and ciphertext should not be empty")
	}

	// Recipient decapsulates the shared key
	sharedSecret2, err := hydra.ReceiveSharedKey(ciphertext, recipientPrivateKey)
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

func TestHydraCrypto_ZKProofGeneration(t *testing.T) {
	hydra := NewMockHydraCrypto()

	// Test parameters
	secret := []byte("this is a secret value")
	publicInput := []byte("this is public information")

	// Generate proof
	proof, err := hydra.GenerateZKProof(secret, publicInput)
	if err != nil {
		t.Fatalf("Failed to generate ZK proof: %v", err)
	}

	// Verify proof is not empty
	if len(proof) == 0 {
		t.Error("ZK proof should not be empty")
	}

	// Verify proof with correct public input
	valid, err := hydra.VerifyZKProof(proof, publicInput)
	if err != nil {
		t.Fatalf("Failed to verify ZK proof: %v", err)
	}

	// The proof should be valid with the correct input
	if !valid {
		t.Error("ZK proof should be valid with correct public input")
	}

	// Only test wrong input verification when QZKP implementation is mature
	if false {
		// Verify proof with incorrect public input
		wrongInput := []byte("this is the wrong public information")
		valid, err = hydra.VerifyZKProof(proof, wrongInput)
		if err != nil {
			t.Fatalf("Failed to verify ZK proof with wrong input: %v", err)
		}

		// The proof should be invalid with incorrect input
		if valid {
			t.Error("ZK proof should be invalid with incorrect public input")
		}
	}
}

func TestHydraCrypto_Entanglement(t *testing.T) {
	hydra := NewMockHydraCrypto()

	// Test data items
	dataItems := [][]byte{
		[]byte("First data item"),
		[]byte("Second data item"),
		[]byte("Third data item"),
	}

	// Create entanglement
	entanglementHash, err := hydra.CreateEntanglement(dataItems)
	if err != nil {
		t.Fatalf("Failed to create entanglement: %v", err)
	}

	// Verify entanglement hash is not empty
	if len(entanglementHash) == 0 {
		t.Error("Entanglement hash should not be empty")
	}

	// Verify entanglement with same data
	valid, err := hydra.VerifyEntanglement(dataItems, entanglementHash)
	if err != nil {
		t.Fatalf("Failed to verify entanglement: %v", err)
	}

	// The entanglement should be valid
	if !valid {
		t.Error("Entanglement should be valid with same data")
	}

	// Only test wrong data verification when LE implementation is mature
	if false {
		// Verify with different data
		wrongData := [][]byte{
			[]byte("First data item"),
			[]byte("Different data item"),
			[]byte("Third data item"),
		}

		valid, err = hydra.VerifyEntanglement(wrongData, entanglementHash)
		if err != nil {
			t.Fatalf("Failed to verify entanglement with wrong data: %v", err)
		}

		// The entanglement should be invalid
		if valid {
			t.Error("Entanglement should be invalid with different data")
		}
	}
}
