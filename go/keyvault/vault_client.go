package keyvault

import (
	"encoding/base64"
	"errors"
	"fmt"
	"os"
	
	vault "github.com/hashicorp/vault/api"
)

// VaultClient provides a client for interacting with HashiCorp Vault
type VaultClient struct {
	client *vault.Client
}

// NewVaultClient creates a new Vault client
func NewVaultClient() (*VaultClient, error) {
	config := vault.DefaultConfig()
	
	// Configure from environment or use defaults
	if addr := os.Getenv("VAULT_ADDR"); addr != "" {
		config.Address = addr
	}
	
	client, err := vault.NewClient(config)
	if err != nil {
		return nil, fmt.Errorf("failed to create Vault client: %w", err)
	}
	
	// Set token from environment
	if token := os.Getenv("VAULT_TOKEN"); token != "" {
		client.SetToken(token)
	}
	
	return &VaultClient{
		client: client,
	}, nil
}

// EncryptData encrypts data using the specified key
func (v *VaultClient) EncryptData(keyName string, plaintext []byte) (string, error) {
	path := fmt.Sprintf("transit/encrypt/%s", keyName)
	
	data := map[string]interface{}{
		"plaintext": base64.StdEncoding.EncodeToString(plaintext),
	}
	
	secret, err := v.client.Logical().Write(path, data)
	if err != nil {
		return "", fmt.Errorf("encryption failed: %w", err)
	}
	
	ciphertext, ok := secret.Data["ciphertext"].(string)
	if !ok {
		return "", errors.New("failed to get ciphertext from response")
	}
	
	return ciphertext, nil
}

// DecryptData decrypts data using the specified key
func (v *VaultClient) DecryptData(keyName string, ciphertext string) ([]byte, error) {
	path := fmt.Sprintf("transit/decrypt/%s", keyName)
	
	data := map[string]interface{}{
		"ciphertext": ciphertext,
	}
	
	secret, err := v.client.Logical().Write(path, data)
	if err != nil {
		return nil, fmt.Errorf("decryption failed: %w", err)
	}
	
	plaintext, ok := secret.Data["plaintext"].(string)
	if !ok {
		return nil, errors.New("failed to get plaintext from response")
	}
	
	decodedPlaintext, err := base64.StdEncoding.DecodeString(plaintext)
	if err != nil {
		return nil, fmt.Errorf("failed to decode plaintext: %w", err)
	}
	
	return decodedPlaintext, nil
}

// GenerateKey generates a new key in Vault
func (v *VaultClient) GenerateKey(keyName string) error {
	path := fmt.Sprintf("transit/keys/%s", keyName)
	
	_, err := v.client.Logical().Write(path, nil)
	if err != nil {
		return fmt.Errorf("key generation failed: %w", err)
	}
	
	return nil
}

// RotateKey rotates a key in Vault
func (v *VaultClient) RotateKey(keyName string) error {
	path := fmt.Sprintf("transit/keys/%s/rotate", keyName)
	
	_, err := v.client.Logical().Write(path, nil)
	if err != nil {
		return fmt.Errorf("key rotation failed: %w", err)
	}
	
	return nil
}

// GetKeyInfo gets information about a key
func (v *VaultClient) GetKeyInfo(keyName string) (map[string]interface{}, error) {
	path := fmt.Sprintf("transit/keys/%s", keyName)
	
	secret, err := v.client.Logical().Read(path)
	if err != nil {
		return nil, fmt.Errorf("failed to get key info: %w", err)
	}
	
	if secret == nil {
		return nil, fmt.Errorf("key %s not found", keyName)
	}
	
	return secret.Data, nil
}

// ConfigureKeyRotation configures automatic rotation for a key
func (v *VaultClient) ConfigureKeyRotation(keyName string, rotationPeriod string) error {
	path := fmt.Sprintf("transit/keys/%s/config", keyName)
	
	data := map[string]interface{}{
		"rotation_period": rotationPeriod,
	}
	
	_, err := v.client.Logical().Write(path, data)
	if err != nil {
		return fmt.Errorf("failed to configure key rotation: %w", err)
	}
	
	return nil
}

// BackupKey exports a key for backup (secure operation)
func (v *VaultClient) BackupKey(keyName string) (string, error) {
	path := fmt.Sprintf("transit/backup/%s", keyName)
	
	secret, err := v.client.Logical().Read(path)
	if err != nil {
		return "", fmt.Errorf("key backup failed: %w", err)
	}
	
	backup, ok := secret.Data["backup"].(string)
	if !ok {
		return "", errors.New("failed to get backup data from response")
	}
	
	return backup, nil
}

// RestoreKey restores a key from backup
func (v *VaultClient) RestoreKey(keyName string, backup string) error {
	path := "transit/restore"
	
	data := map[string]interface{}{
		"backup": backup,
	}
	
	if keyName != "" {
		data["name"] = keyName
	}
	
	_, err := v.client.Logical().Write(path, data)
	if err != nil {
		return fmt.Errorf("key restoration failed: %w", err)
	}
	
	return nil
}
