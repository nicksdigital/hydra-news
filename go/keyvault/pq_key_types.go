package keyvault

import (
	"time"
)

// PQKeyType identifies a post-quantum key type
type PQKeyType string

const (
	// PQKeyTypeKyber is for Kyber key encapsulation
	PQKeyTypeKyber PQKeyType = "kyber"

	// PQKeyTypeFalcon is for Falcon signatures
	PQKeyTypeFalcon PQKeyType = "falcon"
)

// PQKeyInfo contains metadata about a post-quantum key
type PQKeyInfo struct {
	ID           string
	Type         PQKeyType
	Purpose      KeyPurpose
	CreatedAt    time.Time
	ExpiresAt    time.Time
	PublicKey    []byte
	PrivateKey   []byte // Only present for local use, never transmitted
}
