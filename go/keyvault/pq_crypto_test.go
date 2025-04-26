package keyvault

import (
	"bytes"
	"testing"
	"time"
)

// TestPQCryptoManagerInitClose tests that the PQ crypto manager can be initialized and closed
func TestPQCryptoManagerInitClose(t *testing.T) {
	manager, err := NewPQCryptoManager()
	if err != nil {
		t.Fatalf("Failed to initialize PQ crypto manager: %v", err)
	}
	
	// Ensure clean shutdown
	manager.Close()
}

// TestKyberKeyGeneration tests generating and retrieving Kyber keys
func TestKyberKeyGeneration(t *testing.T) {
	manager, err := NewPQCryptoManager()
	if err != nil {
		t.Fatalf("Failed to initialize PQ crypto manager: %v", err)
	}
	defer manager.Close()
	
	// Generate Kyber key
	keyInfo, err := manager.GenerateKyberKey(KeyPurposeEncryption, 30)
	if err != nil {
		t.Fatalf("Failed to generate Kyber key: %v", err)
	}
	
	// Verify key attributes
	if keyInfo.Type != PQKeyTypeKyber {
		t.Errorf("Expected key type %s, got %s", PQKeyTypeKyber, keyInfo.Type)
	}
	
	if keyInfo.Purpose != KeyPurposeEncryption {
		t.Errorf("Expected key purpose %s, got %s", KeyPurposeEncryption, keyInfo.Purpose)
	}
	
	if len(keyInfo.PublicKey) == 0 || len(keyInfo.PrivateKey) == 0 {
		t.Error("Key material should not be empty")
	}
	
	// Verify expiration date is in the future
	if !keyInfo.ExpiresAt.After(time.Now()) {
		t.Error("Key expiration date should be in the future")
	}
	
	// Retrieve the key by ID
	retrievedKey, err := manager.GetKey(keyInfo.ID)
	if err != nil {
		t.Fatalf("Failed to retrieve key: %v", err)
	}
	
	// Verify it's the same key
	if retrievedKey.ID != keyInfo.ID {
		t.Errorf("Retrieved key ID (%s) doesn't match original (%s)", retrievedKey.ID, keyInfo.ID)
	}
	
	if !bytes.Equal(retrievedKey.PublicKey, keyInfo.PublicKey) {
		t.Error("Retrieved public key doesn't match original")
	}
	
	if !bytes.Equal(retrievedKey.PrivateKey, keyInfo.PrivateKey) {
		t.Error("Retrieved private key doesn't match original")
	}
}

// TestFalconKeyGeneration tests generating and retrieving Falcon keys
func TestFalconKeyGeneration(t *testing.T) {
	manager, err := NewPQCryptoManager()
	if err != nil {
		t.Fatalf("Failed to initialize PQ crypto manager: %v", err)
	}
	defer manager.Close()
	
	// Generate Falcon key
	keyInfo, err := manager.GenerateFalconKey(KeyPurposeAuthentication, 60)
	if err != nil {
		t.Fatalf("Failed to generate Falcon key: %v", err)
	}
	
	// Verify key attributes
	if keyInfo.Type != PQKeyTypeFalcon {
		t.Errorf("Expected key type %s, got %s", PQKeyTypeFalcon, keyInfo.Type)
	}
	
	if keyInfo.Purpose != KeyPurposeAuthentication {
		t.Errorf("Expected key purpose %s, got %s", KeyPurposeAuthentication, keyInfo.Purpose)
	}
	
	if len(keyInfo.PublicKey) == 0 || len(keyInfo.PrivateKey) == 0 {
		t.Error("Key material should not be empty")
	}
	
	// Verify expiration date is in the future
	if !keyInfo.ExpiresAt.After(time.Now()) {
		t.Error("Key expiration date should be in the future")
	}
	
	// Retrieve the key by ID
	retrievedKey, err := manager.GetKey(keyInfo.ID)
	if err != nil {
		t.Fatalf("Failed to retrieve key: %v", err)
	}
	
	// Verify it's the same key
	if retrievedKey.ID != keyInfo.ID {
		t.Errorf("Retrieved key ID (%s) doesn't match original (%s)", retrievedKey.ID, keyInfo.ID)
	}
	
	if !bytes.Equal(retrievedKey.PublicKey, keyInfo.PublicKey) {
		t.Error("Retrieved public key doesn't match original")
	}
	
	if !bytes.Equal(retrievedKey.PrivateKey, keyInfo.PrivateKey) {
		t.Error("Retrieved private key doesn't match original")
	}
}

// TestMessageSigning tests signing and verifying messages with Falcon
func TestMessageSigning(t *testing.T) {
	manager, err := NewPQCryptoManager()
	if err != nil {
		t.Fatalf("Failed to initialize PQ crypto manager: %v", err)
	}
	defer manager.Close()
	
	// Generate Falcon key
	keyInfo, err := manager.GenerateFalconKey(KeyPurposeAuthentication, 60)
	if err != nil {
		t.Fatalf("Failed to generate Falcon key: %v", err)
	}
	
	// Test message
	message := []byte("This is a test message for the PQ crypto manager")
	
	// Sign the message
	signature, err := manager.SignMessage(message, keyInfo.ID)
	if err != nil {
		t.Fatalf("Failed to sign message: %v", err)
	}
	
	// Verify signature is not empty
	if len(signature) == 0 {
		t.Error("Signature should not be empty")
	}
	
	// Verify the signature
	valid, err := manager.VerifySignature(message, signature, keyInfo.ID)
	if err != nil {
		t.Fatalf("Failed to verify signature: %v", err)
	}
	
	// The signature should be valid
	if !valid {
		t.Error("Signature should be valid")
	}
	
	// Verify with incorrect message
	wrongMessage := []byte("This is NOT the test message that was signed")
	valid, err = manager.VerifySignature(wrongMessage, signature, keyInfo.ID)
	if err != nil {
		t.Fatalf("Failed to verify signature with wrong message: %v", err)
	}
	
	// The signature should be invalid
	if valid {
		t.Error("Signature should be invalid with incorrect message")
	}
}

// TestKeyExchange tests key exchange with Kyber
func TestKeyExchange(t *testing.T) {
	manager, err := NewPQCryptoManager()
	if err != nil {
		t.Fatalf("Failed to initialize PQ crypto manager: %v", err)
	}
	defer manager.Close()
	
	// Generate Kyber key for recipient
	recipientKey, err := manager.GenerateKyberKey(KeyPurposeEncryption, 30)
	if err != nil {
		t.Fatalf("Failed to generate recipient Kyber key: %v", err)
	}
	
	// Sender establishes a shared key
	sharedSecret1, ciphertext, err := manager.EstablishSharedKey(recipientKey.ID)
	if err != nil {
		t.Fatalf("Failed to establish shared key: %v", err)
	}
	
	// Verify shared secret and ciphertext are not empty
	if len(sharedSecret1) == 0 || len(ciphertext) == 0 {
		t.Error("Shared secret and ciphertext should not be empty")
	}
	
	// Recipient receives the shared key
	sharedSecret2, err := manager.ReceiveSharedKey(recipientKey.ID, ciphertext)
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

// TestKeyDeletion tests deleting keys
func TestKeyDeletion(t *testing.T) {
	manager, err := NewPQCryptoManager()
	if err != nil {
		t.Fatalf("Failed to initialize PQ crypto manager: %v", err)
	}
	defer manager.Close()
	
	// Generate key
	keyInfo, err := manager.GenerateKyberKey(KeyPurposeEncryption, 30)
	if err != nil {
		t.Fatalf("Failed to generate key: %v", err)
	}
	
	// Delete the key
	err = manager.DeleteKey(keyInfo.ID)
	if err != nil {
		t.Fatalf("Failed to delete key: %v", err)
	}
	
	// Try to retrieve the deleted key
	_, err = manager.GetKey(keyInfo.ID)
	if err == nil {
		t.Error("Expected error when retrieving deleted key, got nil")
	}
}

// TestKeyManagerIntegration tests integration with the KeyManager
func TestKeyManagerIntegration(t *testing.T) {
	// Create a key manager with nil vault client (we're not testing vault integration)
	keyManager := NewKeyManager(nil)
	
	// Generate Kyber key
	kyberKey, err := keyManager.GenerateKyberKey(KeyPurposeEncryption, 30)
	if err != nil {
		t.Fatalf("Failed to generate Kyber key through KeyManager: %v", err)
	}
	
	// Generate Falcon key
	falconKey, err := keyManager.GenerateFalconKey(KeyPurposeAuthentication, 60)
	if err != nil {
		t.Fatalf("Failed to generate Falcon key through KeyManager: %v", err)
	}
	
	// Test message
	message := []byte("This is a test message for KeyManager integration")
	
	// Sign the message
	signature, err := keyManager.SignWithFalcon(message, falconKey.ID)
	if err != nil {
		t.Fatalf("Failed to sign message through KeyManager: %v", err)
	}
	
	// Verify the signature
	valid, err := keyManager.VerifyFalconSignature(message, signature, falconKey.ID)
	if err != nil {
		t.Fatalf("Failed to verify signature through KeyManager: %v", err)
	}
	
	// The signature should be valid
	if !valid {
		t.Error("Signature should be valid")
	}
	
	// Establish Kyber shared key
	sharedSecret1, ciphertext, err := keyManager.EstablishKyberSharedKey(kyberKey.ID)
	if err != nil {
		t.Fatalf("Failed to establish shared key through KeyManager: %v", err)
	}
	
	// Receive Kyber shared key
	sharedSecret2, err := keyManager.ReceiveKyberSharedKey(kyberKey.ID, ciphertext)
	if err != nil {
		t.Fatalf("Failed to receive shared key through KeyManager: %v", err)
	}
	
	// Shared secrets should match
	if !bytes.Equal(sharedSecret1, sharedSecret2) {
		t.Error("Shared secrets should match between sender and recipient")
	}
	
	// Clean up
	keyManager.Close()
}
