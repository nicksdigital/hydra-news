package keyvault

import (
	"crypto/rand"
	"encoding/hex"
	"errors"
	"fmt"
	"sync"
	"time"
)

// KeyPurpose defines the purpose of a cryptographic key
type KeyPurpose string

const (
	// KeyPurposeEncryption is for data encryption
	KeyPurposeEncryption KeyPurpose = "encryption"

	// KeyPurposeAuthentication is for data authentication
	KeyPurposeAuthentication KeyPurpose = "authentication"

	// KeyPurposeIdentity is for identity-related operations
	KeyPurposeIdentity KeyPurpose = "identity"

	// KeyPurposeSourceProtection is for source protection
	KeyPurposeSourceProtection KeyPurpose = "source_protection"
)

// KeyType defines the type of cryptographic key
type KeyType string

const (
	// KeyTypeAES is for AES keys
	KeyTypeAES KeyType = "aes"

	// KeyTypeRSA is for RSA keys
	KeyTypeRSA KeyType = "rsa"

	// KeyTypeED25519 is for ED25519 keys
	KeyTypeED25519 KeyType = "ed25519"

	// KeyTypeKyber is for Kyber post-quantum keys
	KeyTypeKyber KeyType = "kyber"

	// KeyTypeFalcon is for Falcon post-quantum keys
	KeyTypeFalcon KeyType = "falcon"
)

// KeyInfo contains metadata about a key
type KeyInfo struct {
	Name         string
	Type         KeyType
	Purpose      KeyPurpose
	CreatedAt    time.Time
	LastRotated  time.Time
	NextRotation time.Time
	Version      int
}

// KeyManager manages cryptographic keys for the system
type KeyManager struct {
	vaultClient    *VaultClient
	pqCryptoManager *PQCryptoManager
	keyCache       map[string][]byte
	cacheExpiry    map[string]time.Time
	cacheMutex     sync.RWMutex
	cacheTTL       time.Duration
	rotationFreq   map[KeyPurpose]time.Duration
}

// NewKeyManager creates a new key manager
func NewKeyManager(vaultClient *VaultClient) *KeyManager {
	// Define default rotation frequencies based on key purpose
	rotationFreq := map[KeyPurpose]time.Duration{
		KeyPurposeEncryption:       30 * 24 * time.Hour, // 30 days
		KeyPurposeAuthentication:   60 * 24 * time.Hour, // 60 days
		KeyPurposeIdentity:         90 * 24 * time.Hour, // 90 days
		KeyPurposeSourceProtection: 90 * 24 * time.Hour, // 90 days
	}

	// Initialize the post-quantum crypto manager
	pqCryptoManager, err := NewPQCryptoManager()
	if err != nil {
		// Log error but continue - we'll operate without PQ crypto if necessary
		fmt.Printf("Failed to initialize post-quantum crypto manager: %v\n", err)
	}

	return &KeyManager{
		vaultClient:    vaultClient,
		pqCryptoManager: pqCryptoManager,
		keyCache:       make(map[string][]byte),
		cacheExpiry:    make(map[string]time.Time),
		cacheTTL:       15 * time.Minute, // Cache keys for 15 minutes
		rotationFreq:   rotationFreq,
	}
}

// CreateKey creates a new key in the key management system
func (km *KeyManager) CreateKey(name string, keyType KeyType, purpose KeyPurpose) error {
	// Generate a Vault key name
	vaultKeyName := fmt.Sprintf("%s_%s", purpose, name)

	// Create the key in Vault
	err := km.vaultClient.GenerateKey(vaultKeyName)
	if err != nil {
		return fmt.Errorf("failed to create key %s: %w", name, err)
	}

	// Configure key rotation based on purpose
	rotationPeriod := km.rotationFreq[purpose].String()
	err = km.vaultClient.ConfigureKeyRotation(vaultKeyName, rotationPeriod)
	if err != nil {
		return fmt.Errorf("failed to configure key rotation for %s: %w", name, err)
	}

	return nil
}

// GetKey retrieves a key by name (from cache if available)
func (km *KeyManager) GetKey(name string, purpose KeyPurpose) ([]byte, error) {
	vaultKeyName := fmt.Sprintf("%s_%s", purpose, name)

	// Check cache first
	km.cacheMutex.RLock()
	cachedKey, hasCachedKey := km.keyCache[vaultKeyName]
	expiry, hasExpiry := km.cacheExpiry[vaultKeyName]
	km.cacheMutex.RUnlock()

	// If key is in cache and not expired, return it
	if hasCachedKey && hasExpiry && time.Now().Before(expiry) {
		return cachedKey, nil
	}

	// Key not in cache or expired, fetch from Vault
	// In a real implementation, this would use the Vault client to fetch the actual key
	// For demonstration purposes, we'll generate a random key
	key := make([]byte, 32) // 256-bit key
	_, err := rand.Read(key)
	if err != nil {
		return nil, fmt.Errorf("failed to generate key: %w", err)
	}

	// Update cache
	km.cacheMutex.Lock()
	km.keyCache[vaultKeyName] = key
	km.cacheExpiry[vaultKeyName] = time.Now().Add(km.cacheTTL)
	km.cacheMutex.Unlock()

	return key, nil
}

// RotateKey manually rotates a key
func (km *KeyManager) RotateKey(name string, purpose KeyPurpose) error {
	vaultKeyName := fmt.Sprintf("%s_%s", purpose, name)

	// Rotate the key in Vault
	err := km.vaultClient.RotateKey(vaultKeyName)
	if err != nil {
		return fmt.Errorf("failed to rotate key %s: %w", name, err)
	}

	// Remove from cache if present
	km.cacheMutex.Lock()
	delete(km.keyCache, vaultKeyName)
	delete(km.cacheExpiry, vaultKeyName)
	km.cacheMutex.Unlock()

	return nil
}

// GetKeyInfo gets information about a key
func (km *KeyManager) GetKeyInfo(name string, purpose KeyPurpose) (*KeyInfo, error) {
	vaultKeyName := fmt.Sprintf("%s_%s", purpose, name)

	// Get key info from Vault
	_, err := km.vaultClient.GetKeyInfo(vaultKeyName)
	if err != nil {
		return nil, fmt.Errorf("failed to get key info for %s: %w", name, err)
	}
	// Parse key info
	// In a real implementation, this would parse the response from Vault
	// For demonstration purposes, we'll create a mock KeyInfo
	info := &KeyInfo{
		Name:         name,
		Type:         "mock-type", // Use a string literal or appropriate value
		Purpose:      purpose,
		CreatedAt:    time.Now().Add(-30 * 24 * time.Hour), // Mock creation 30 days ago
		LastRotated:  time.Now().Add(-15 * 24 * time.Hour), // Mock last rotation 15 days ago
		NextRotation: time.Now().Add(15 * 24 * time.Hour),  // Mock next rotation in 15 days
	}
	return info, nil
}

// EncryptData encrypts data using a key
func (km *KeyManager) EncryptData(data []byte, keyName string, purpose KeyPurpose) (string, error) {
	vaultKeyName := fmt.Sprintf("%s_%s", purpose, keyName)

	// Use Vault transit engine to encrypt
	ciphertext, err := km.vaultClient.EncryptData(vaultKeyName, data)
	if err != nil {
		return "", fmt.Errorf("encryption failed: %w", err)
	}

	return ciphertext, nil
}

// DecryptData decrypts data using a key
func (km *KeyManager) DecryptData(ciphertext string, keyName string, purpose KeyPurpose) ([]byte, error) {
	vaultKeyName := fmt.Sprintf("%s_%s", purpose, keyName)

	// Use Vault transit engine to decrypt
	plaintext, err := km.vaultClient.DecryptData(vaultKeyName, ciphertext)
	if err != nil {
		return nil, fmt.Errorf("decryption failed: %w", err)
	}

	return plaintext, nil
}

// BackupKey backs up a key
func (km *KeyManager) BackupKey(name string, purpose KeyPurpose) (string, error) {
	vaultKeyName := fmt.Sprintf("%s_%s", purpose, name)

	// Backup the key from Vault
	backup, err := km.vaultClient.BackupKey(vaultKeyName)
	if err != nil {
		return "", fmt.Errorf("key backup failed: %w", err)
	}

	return backup, nil
}

// RestoreKey restores a key from backup
func (km *KeyManager) RestoreKey(backup string, name string, purpose KeyPurpose) error {
	vaultKeyName := fmt.Sprintf("%s_%s", purpose, name)

	// Restore the key to Vault
	err := km.vaultClient.RestoreKey(vaultKeyName, backup)
	if err != nil {
		return fmt.Errorf("key restoration failed: %w", err)
	}

	return nil
}

// GenerateTempKey generates a temporary key for session use
func (km *KeyManager) GenerateTempKey(length int) (string, error) {
	keyBytes := make([]byte, length)
	_, err := rand.Read(keyBytes)
	if err != nil {
		return "", fmt.Errorf("failed to generate temporary key: %w", err)
	}

	return hex.EncodeToString(keyBytes), nil
}

// GenerateKyberKey generates a post-quantum secure Kyber key pair
func (km *KeyManager) GenerateKyberKey(purpose KeyPurpose, validityDays int) (*PQKeyInfo, error) {
	if km.pqCryptoManager == nil {
		return nil, errors.New("post-quantum crypto manager is not initialized")
	}
	
	return km.pqCryptoManager.GenerateKyberKey(purpose, validityDays)
}

// GenerateFalconKey generates a post-quantum secure Falcon signature key pair
func (km *KeyManager) GenerateFalconKey(purpose KeyPurpose, validityDays int) (*PQKeyInfo, error) {
	if km.pqCryptoManager == nil {
		return nil, errors.New("post-quantum crypto manager is not initialized")
	}
	
	return km.pqCryptoManager.GenerateFalconKey(purpose, validityDays)
}

// GetPQKey retrieves a post-quantum key by ID
func (km *KeyManager) GetPQKey(id string) (*PQKeyInfo, error) {
	if km.pqCryptoManager == nil {
		return nil, errors.New("post-quantum crypto manager is not initialized")
	}
	
	return km.pqCryptoManager.GetKey(id)
}

// SignWithFalcon signs a message using a Falcon post-quantum signature
func (km *KeyManager) SignWithFalcon(message []byte, keyID string) ([]byte, error) {
	if km.pqCryptoManager == nil {
		return nil, errors.New("post-quantum crypto manager is not initialized")
	}
	
	return km.pqCryptoManager.SignMessage(message, keyID)
}

// VerifyFalconSignature verifies a Falcon post-quantum signature
func (km *KeyManager) VerifyFalconSignature(message, signature []byte, keyID string) (bool, error) {
	if km.pqCryptoManager == nil {
		return false, errors.New("post-quantum crypto manager is not initialized")
	}
	
	return km.pqCryptoManager.VerifySignature(message, signature, keyID)
}

// EstablishKyberSharedKey establishes a shared key using Kyber post-quantum KEM
func (km *KeyManager) EstablishKyberSharedKey(recipientKeyID string) ([]byte, []byte, error) {
	if km.pqCryptoManager == nil {
		return nil, nil, errors.New("post-quantum crypto manager is not initialized")
	}
	
	return km.pqCryptoManager.EstablishSharedKey(recipientKeyID)
}

// ReceiveKyberSharedKey decapsulates a Kyber ciphertext to obtain a shared key
func (km *KeyManager) ReceiveKyberSharedKey(recipientKeyID string, ciphertext []byte) ([]byte, error) {
	if km.pqCryptoManager == nil {
		return nil, errors.New("post-quantum crypto manager is not initialized")
	}
	
	return km.pqCryptoManager.ReceiveSharedKey(recipientKeyID, ciphertext)
}

// StartKeyRotationService starts a service to automatically rotate keys
func (km *KeyManager) StartKeyRotationService(interval time.Duration) {
	go func() {
		ticker := time.NewTicker(interval)
		defer ticker.Stop()

		for {
			<-ticker.C
			km.rotateExpiredKeys()
		}
	}()
}

// rotateExpiredKeys checks for and rotates any keys that are due for rotation
func (km *KeyManager) rotateExpiredKeys() {
	// In a real implementation, this would query Vault for keys that need rotation
	// For demonstration purposes, we'll just log a message
	fmt.Println("Checking for keys that need rotation...")
	
	// Also check post-quantum keys for rotation if available
	if km.pqCryptoManager != nil {
		fmt.Println("Checking post-quantum keys for rotation...")
		// For a real implementation, we would check and rotate PQ keys here
	}
}

// Close cleans up resources used by the key manager
func (km *KeyManager) Close() {
	// Clean up post-quantum crypto manager if it exists
	if km.pqCryptoManager != nil {
		km.pqCryptoManager.Close()
		km.pqCryptoManager = nil
	}
	
	// Clear any cached keys
	km.cacheMutex.Lock()
	defer km.cacheMutex.Unlock()
	
	for k := range km.keyCache {
		delete(km.keyCache, k)
	}
	
	for k := range km.cacheExpiry {
		delete(km.cacheExpiry, k)
	}
}
