package database

import (
	"time"
)

// NewsContent represents a news article or content item
type NewsContent struct {
	ContentHash      string    `json:"content_hash"`
	Title            string    `json:"title"`
	Content          string    `json:"content"`
	Source           string    `json:"source"`
	Author           string    `json:"author,omitempty"`
	PublishDate      time.Time `json:"publish_date,omitempty"`
	URL              string    `json:"url,omitempty"`
	EntanglementHash string    `json:"entanglement_hash"`
	CreatedAt        time.Time `json:"created_at"`
	UpdatedAt        time.Time `json:"updated_at"`
	SubmissionIP     string    `json:"submission_ip,omitempty"`
	SubmitterID      string    `json:"submitter_id,omitempty"`
	IsVerified       bool      `json:"is_verified"`
	Entities         []*Entity `json:"entities,omitempty"`
	Claims           []*Claim  `json:"claims,omitempty"`
	Verification     *Verification `json:"verification,omitempty"`
}

// Entity represents an entity extracted from content
type Entity struct {
	EntityID      string    `json:"entity_id"`
	ContentHash   string    `json:"content_hash"`
	Name          string    `json:"name"`
	Type          string    `json:"type"`
	Confidence    float64   `json:"confidence"`
	Context       string    `json:"context,omitempty"`
	PositionStart int       `json:"position_start,omitempty"`
	PositionEnd   int       `json:"position_end,omitempty"`
	CreatedAt     time.Time `json:"created_at"`
}

// Claim represents a factual claim extracted from content
type Claim struct {
	ClaimID       string    `json:"claim_id"`
	ContentHash   string    `json:"content_hash"`
	ClaimText     string    `json:"claim_text"`
	SourceText    string    `json:"source_text,omitempty"`
	Confidence    float64   `json:"confidence"`
	ClaimType     string    `json:"claim_type"`
	PositionStart int       `json:"position_start,omitempty"`
	PositionEnd   int       `json:"position_end,omitempty"`
	CreatedAt     time.Time `json:"created_at"`
	Entities      []string  `json:"entities,omitempty"` // List of entity IDs related to this claim
}

// Verification represents a verification result for content
type Verification struct {
	VerificationID    string      `json:"verification_id"`
	ContentHash       string      `json:"content_hash"`
	VerificationScore float64     `json:"verification_score"`
	VerificationTime  time.Time   `json:"verification_time"`
	VerifierNodeID    string      `json:"verifier_node_id"`
	ConsensusRoundID  string      `json:"consensus_round_id,omitempty"`
	VerificationStatus string     `json:"verification_status"`
	References        []*Reference `json:"references,omitempty"`
}

// Reference represents a reference used for cross-checking content
type Reference struct {
	ReferenceID      string    `json:"reference_id"`
	VerificationID   string    `json:"verification_id"`
	ContentHash      string    `json:"content_hash"`
	ReferenceURL     string    `json:"reference_url"`
	ReferenceTitle   string    `json:"reference_title,omitempty"`
	ReferenceSource  string    `json:"reference_source,omitempty"`
	ReferenceHash    string    `json:"reference_hash,omitempty"`
	SupportScore     float64   `json:"support_score,omitempty"`
	DisputeScore     float64   `json:"dispute_score,omitempty"`
	CreatedAt        time.Time `json:"created_at"`
}

// Node represents a node in the consensus network
type Node struct {
	NodeID        string    `json:"node_id"`
	NodeAddress   string    `json:"node_address"`
	QZKPAddress   string    `json:"qzkp_address"`
	PublicKey     string    `json:"public_key"`
	Reputation    float64   `json:"reputation"`
	FirstSeen     time.Time `json:"first_seen"`
	LastSeen      time.Time `json:"last_seen"`
	Status        string    `json:"status"`
	GeoRegion     string    `json:"geo_region,omitempty"`
	NodeVersion   string    `json:"node_version,omitempty"`
	IsBootstrap   bool      `json:"is_bootstrap"`
}

// User represents a user in the system
type User struct {
	UserID      string    `json:"user_id"`
	Username    string    `json:"username"`
	Email       string    `json:"email,omitempty"`
	Role        string    `json:"role"`
	DisplayName string    `json:"display_name,omitempty"`
	Reputation  float64   `json:"reputation"`
	CreatedAt   time.Time `json:"created_at"`
	LastLogin   time.Time `json:"last_login,omitempty"`
	IsActive    bool      `json:"is_active"`
	PublicKey   string    `json:"public_key,omitempty"`
}

// Credential represents a cryptographic credential for a user
type Credential struct {
	CredentialID   string    `json:"credential_id"`
	UserID         string    `json:"user_id"`
	QZKPProof      string    `json:"qzkp_proof"`
	IssuedAt       time.Time `json:"issued_at"`
	ExpiresAt      time.Time `json:"expires_at"`
	CredentialType string    `json:"credential_type"`
	IsRevoked      bool      `json:"is_revoked"`
}

// Source represents a news source
type Source struct {
	SourceID   string    `json:"source_id"`
	SourceName string    `json:"source_name"`
	Domain     string    `json:"domain,omitempty"`
	TrustScore float64   `json:"trust_score"`
	Verified   bool      `json:"verified"`
	CreatedAt  time.Time `json:"created_at"`
	UpdatedAt  time.Time `json:"updated_at"`
}

// ConsensusLog represents a log entry for consensus operations
type ConsensusLog struct {
	LogID    string    `json:"log_id"`
	RoundID  string    `json:"round_id"`
	NodeID   string    `json:"node_id"`
	LogTime  time.Time `json:"log_time"`
	Action   string    `json:"action"`
	Status   string    `json:"status"`
	Details  string    `json:"details,omitempty"`
}

// SystemEvent represents a system event
type SystemEvent struct {
	EventID   string    `json:"event_id"`
	EventType string    `json:"event_type"`
	EventTime time.Time `json:"event_time"`
	Severity  string    `json:"severity"`
	Details   string    `json:"details,omitempty"`
	NodeID    string    `json:"node_id,omitempty"`
}
