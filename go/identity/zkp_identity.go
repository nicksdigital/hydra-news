// Package identity implements the source protection and identity verification
// service for Hydra News, based on Quantum-ZKP principles.
package identity

import (
	"bytes"
	"crypto/ed25519"
	"crypto/rand"
	"crypto/sha256"
	"encoding/base64"
	"encoding/json"
	"errors"
	"fmt"
	"math"
	"time"
)

// GeolocationData represents location information that can be verified
// while preserving privacy
type GeolocationData struct {
	// Only store truncated coordinates to protect exact location
	LatitudeTruncated  float64 `json:"lat_truncated"`
	LongitudeTruncated float64 `json:"lng_truncated"`
	CountryCode        string  `json:"country_code"`
	RegionCode         string  `json:"region_code"`

	// Private fields not included in JSON output
	exactLatitude  float64
	exactLongitude float64
}

// SourceIdentity represents a verified news source with privacy protection
type SourceIdentity struct {
	ID              string    `json:"id"`
	PublicKey       []byte    `json:"public_key"`
	CredentialLevel int       `json:"credential_level"`
	CreatedAt       time.Time `json:"created_at"`
	LastVerified    time.Time `json:"last_verified"`

	// These fields are stored but not exposed in JSON
	privateKey    ed25519.PrivateKey
	geolocation   *GeolocationData
	zkpCommitment []byte
}

// ZKPSession represents an ongoing zero-knowledge proof verification session
type ZKPSession struct {
	ID            string    `json:"id"`
	SourceID      string    `json:"source_id"`
	ChallengeData []byte    `json:"challenge_data"`
	CreatedAt     time.Time `json:"created_at"`
	ExpiresAt     time.Time `json:"expires_at"`
	Completed     bool      `json:"completed"`

	// Internal verification data
	expectedResponse []byte
}

// IdentityService manages source identities and verification
type IdentityService struct {
	sources         map[string]*SourceIdentity
	sessions        map[string]*ZKPSession
	zeroKnowledge   *ZeroKnowledgeProvider
	geoVerifier     *GeolocationVerifier
	sessionDuration time.Duration
}

// NewIdentityService creates a new identity service
func NewIdentityService() (*IdentityService, error) {
	zkp, err := NewZeroKnowledgeProvider()
	if err != nil {
		return nil, fmt.Errorf("failed to initialize zero-knowledge provider: %v", err)
	}

	geoVerifier, err := NewGeolocationVerifier()
	if err != nil {
		return nil, fmt.Errorf("failed to initialize geolocation verifier: %v", err)
	}

	return &IdentityService{
		sources:         make(map[string]*SourceIdentity),
		sessions:        make(map[string]*ZKPSession),
		zeroKnowledge:   zkp,
		geoVerifier:     geoVerifier,
		sessionDuration: 30 * time.Minute,
	}, nil
}

// CreateSourceIdentity creates a new source identity with privacy protection
func (s *IdentityService) CreateSourceIdentity(
	credentialLevel int,
	latitude, longitude float64,
	countryCode, regionCode string,
) (*SourceIdentity, error) {
	// Generate key pair
	publicKey, privateKey, err := ed25519.GenerateKey(rand.Reader)
	if err != nil {
		return nil, fmt.Errorf("failed to generate key pair: %v", err)
	}

	// Create geolocation data with privacy protection
	geolocation := &GeolocationData{
		LatitudeTruncated:  truncateCoordinate(latitude),
		LongitudeTruncated: truncateCoordinate(longitude),
		CountryCode:        countryCode,
		RegionCode:         regionCode,
		exactLatitude:      latitude,
		exactLongitude:     longitude,
	}

	// Generate ZKP commitment for geolocation
	zkpCommitment, err := s.zeroKnowledge.CreateGeolocationCommitment(
		latitude, longitude, countryCode, regionCode,
	)
	if err != nil {
		return nil, fmt.Errorf("failed to create ZKP commitment: %v", err)
	}

	// Generate a unique ID
	idHash := sha256.Sum256(append(publicKey, []byte(time.Now().String())...))
	id := base64.URLEncoding.EncodeToString(idHash[:])[:16]

	// Create source identity
	source := &SourceIdentity{
		ID:              id,
		PublicKey:       publicKey,
		CredentialLevel: credentialLevel,
		CreatedAt:       time.Now(),
		LastVerified:    time.Now(),
		privateKey:      privateKey,
		geolocation:     geolocation,
		zkpCommitment:   zkpCommitment,
	}

	// Store the source
	s.sources[id] = source

	return source, nil
}

// StartVerification begins a ZKP-based identity verification process
func (s *IdentityService) StartVerification(sourceID string) (*ZKPSession, error) {
	source, exists := s.sources[sourceID]
	if !exists {
		return nil, errors.New("source not found")
	}

	// Generate challenge data
	challengeData := make([]byte, 32)
	if _, err := rand.Read(challengeData); err != nil {
		return nil, fmt.Errorf("failed to generate challenge: %v", err)
	}

	// Calculate expected response (which only the real source can produce)
	// In a real implementation, this would be more complex and use the ZKP protocol
	expectedResponse := ed25519.Sign(source.privateKey, challengeData)

	// Create session ID
	sessionHash := sha256.Sum256(append(challengeData, []byte(sourceID)...))
	sessionID := base64.URLEncoding.EncodeToString(sessionHash[:])[:16]

	// Create session
	session := &ZKPSession{
		ID:               sessionID,
		SourceID:         sourceID,
		ChallengeData:    challengeData,
		CreatedAt:        time.Now(),
		ExpiresAt:        time.Now().Add(s.sessionDuration),
		Completed:        false,
		expectedResponse: expectedResponse,
	}

	// Store session
	s.sessions[sessionID] = session

	return session, nil
}

// CompleteVerification verifies a source's response to a ZKP challenge
func (s *IdentityService) CompleteVerification(
	sessionID string,
	response []byte,
	latitude, longitude float64,
) (bool, error) {
	session, exists := s.sessions[sessionID]
	if !exists {
		return false, errors.New("session not found")
	}

	if session.Completed {
		return false, errors.New("session already completed")
	}

	if time.Now().After(session.ExpiresAt) {
		return false, errors.New("session expired")
	}

	source, exists := s.sources[session.SourceID]
	if !exists {
		return false, errors.New("source not found")
	}

	// Verify the cryptographic response
	// In a real implementation, this would use the ZKP verification protocol
	if !bytes.Equal(session.expectedResponse, response) {
		return false, nil
	}

	// Verify geolocation is within acceptable range of the registered location
	geoValid, err := s.geoVerifier.VerifyLocation(
		latitude, longitude,
		source.geolocation.exactLatitude, source.geolocation.exactLongitude,
	)
	if err != nil {
		return false, fmt.Errorf("geolocation verification error: %v", err)
	}

	if !geoValid {
		return false, nil
	}

	// Update verification timestamp
	source.LastVerified = time.Now()

	// Mark session as completed
	session.Completed = true

	return true, nil
}

// GenerateAnonymousCredential creates an anonymous credential for a verified source
func (s *IdentityService) GenerateAnonymousCredential(sourceID string) ([]byte, error) {
	source, exists := s.sources[sourceID]
	if !exists {
		return nil, errors.New("source not found")
	}

	// Check if source was recently verified
	if time.Since(source.LastVerified) > 24*time.Hour {
		return nil, errors.New("source must be recently verified")
	}

	// Create credential data (without identifying information)
	credential := struct {
		CredentialLevel int       `json:"level"`
		IssuedAt        time.Time `json:"issued_at"`
		ExpiresAt       time.Time `json:"expires_at"`
		Nonce           string    `json:"nonce"`
	}{
		CredentialLevel: source.CredentialLevel,
		IssuedAt:        time.Now(),
		ExpiresAt:       time.Now().Add(7 * 24 * time.Hour),
		Nonce:           generateNonce(),
	}

	// Serialize credential
	credentialJSON, err := json.Marshal(credential)
	if err != nil {
		return nil, fmt.Errorf("failed to serialize credential: %v", err)
	}

	// Sign the credential
	signature := ed25519.Sign(source.privateKey, credentialJSON)

	// Create signed credential
	signedCredential := struct {
		Credential []byte `json:"credential"`
		Signature  []byte `json:"signature"`
		PublicKey  []byte `json:"public_key"`
	}{
		Credential: credentialJSON,
		Signature:  signature,
		PublicKey:  source.PublicKey,
	}

	// Serialize signed credential
	signedCredentialJSON, err := json.Marshal(signedCredential)
	if err != nil {
		return nil, fmt.Errorf("failed to serialize signed credential: %v", err)
	}

	return signedCredentialJSON, nil
}

// VerifyAnonymousCredential checks if a credential is valid
func (s *IdentityService) VerifyAnonymousCredential(credentialData []byte) (bool, int, error) {
	// Parse signed credential
	var signedCredential struct {
		Credential []byte `json:"credential"`
		Signature  []byte `json:"signature"`
		PublicKey  []byte `json:"public_key"`
	}

	if err := json.Unmarshal(credentialData, &signedCredential); err != nil {
		return false, 0, fmt.Errorf("failed to parse credential: %v", err)
	}

	// Verify signature
	if !ed25519.Verify(
		signedCredential.PublicKey,
		signedCredential.Credential,
		signedCredential.Signature,
	) {
		return false, 0, nil
	}

	// Parse credential content
	var credential struct {
		CredentialLevel int       `json:"level"`
		IssuedAt        time.Time `json:"issued_at"`
		ExpiresAt       time.Time `json:"expires_at"`
		Nonce           string    `json:"nonce"`
	}

	if err := json.Unmarshal(signedCredential.Credential, &credential); err != nil {
		return false, 0, fmt.Errorf("failed to parse credential content: %v", err)
	}

	// Check if credential is expired
	if time.Now().After(credential.ExpiresAt) {
		return false, 0, nil
	}

	return true, credential.CredentialLevel, nil
}

// GetSourcePublicInfo gets public information about a source
func (s *IdentityService) GetSourcePublicInfo(sourceID string) (map[string]interface{}, error) {
	source, exists := s.sources[sourceID]
	if !exists {
		return nil, errors.New("source not found")
	}

	// Return only public information
	return map[string]interface{}{
		"id":               source.ID,
		"credential_level": source.CredentialLevel,
		"created_at":       source.CreatedAt,
		"location": map[string]interface{}{
			"lat_truncated": source.geolocation.LatitudeTruncated,
			"lng_truncated": source.geolocation.LongitudeTruncated,
			"country_code":  source.geolocation.CountryCode,
			"region_code":   source.geolocation.RegionCode,
		},
	}, nil
}

// Helper functions

// truncateCoordinate truncates a coordinate to reduce precision for privacy
func truncateCoordinate(coord float64) float64 {
	// Truncate to approximately 10km precision
	return float64(int(coord*10)) / 10
}

// generateNonce generates a random nonce for credentials
func generateNonce() string {
	nonceBytes := make([]byte, 16)
	rand.Read(nonceBytes)
	return base64.URLEncoding.EncodeToString(nonceBytes)
}

// ZeroKnowledgeProvider interfaces with the C library for ZKP operations
type ZeroKnowledgeProvider struct {
	initialized bool
	qzkpProvider *QZKPProvider
}

// NewZeroKnowledgeProvider creates a new ZKP provider
func NewZeroKnowledgeProvider() (*ZeroKnowledgeProvider, error) {
	// Initialize the QZKP provider through CGO
	qzkpProvider, err := NewQZKPProvider()
	if err != nil {
		return nil, fmt.Errorf("failed to initialize QZKP provider: %v", err)
	}

	return &ZeroKnowledgeProvider{
		initialized: true,
		qzkpProvider: qzkpProvider,
	}, nil
}

// CreateGeolocationCommitment creates a ZKP commitment for geolocation
func (z *ZeroKnowledgeProvider) CreateGeolocationCommitment(
	latitude, longitude float64,
	countryCode, regionCode string,
) ([]byte, error) {
	if !z.initialized {
		return nil, errors.New("ZKP provider not initialized")
	}

	// Call the C library through our CGO binding
	commitment, err := z.qzkpProvider.CreateGeolocationCommitment(
		latitude, longitude, countryCode, regionCode,
	)
	if err != nil {
		// Fall back to simple implementation if C library fails
		locationVector := fmt.Sprintf(
			"[%f,%f,\"%s\",\"%s\"]",
			latitude, longitude, countryCode, regionCode,
		)
		commitmentHash := sha256.Sum256([]byte(locationVector))
		return commitmentHash[:], nil
	}

	return commitment, nil
}

// GeolocationVerifier verifies location claims while preserving privacy
type GeolocationVerifier struct {
	maxDistanceKm float64
}

// NewGeolocationVerifier creates a new geolocation verifier
func NewGeolocationVerifier() (*GeolocationVerifier, error) {
	return &GeolocationVerifier{
		maxDistanceKm: 25.0, // Allow up to 25km deviation for privacy
	}, nil
}

// VerifyLocation checks if a claimed location is valid
func (g *GeolocationVerifier) VerifyLocation(
	claimedLat, claimedLng float64,
	registeredLat, registeredLng float64,
) (bool, error) {
	// Calculate distance between points
	distance := calculateDistance(
		claimedLat, claimedLng,
		registeredLat, registeredLng,
	)

	// Check if distance is within acceptable range
	return distance <= g.maxDistanceKm, nil
}

// calculateDistance calculates haversine distance between two points in km
func calculateDistance(lat1, lng1, lat2, lng2 float64) float64 {
	const earthRadiusKm = 6371.0

	// Convert degrees to radians
	lat1Rad := lat1 * (3.141592653589793 / 180.0)
	lng1Rad := lng1 * (3.141592653589793 / 180.0)
	lat2Rad := lat2 * (3.141592653589793 / 180.0)
	lng2Rad := lng2 * (3.141592653589793 / 180.0)

	// Haversine formula
	dlat := lat2Rad - lat1Rad
	dlng := lng2Rad - lng1Rad
	a := (1 - CosDeg(dlat)) + CosDeg(lat1Rad)*CosDeg(lat2Rad)*(1-CosDeg(dlng))
	c := 2 * AsinDeg(MinDeg(1, SqrtDeg(a)))

	return earthRadiusKm * c
}

// Math helpers that don't use math.* functions to avoid CGO
func SqrtDeg(x float64) float64 {
	// Simple approximation for square root
	z := x / 2.0
	for i := 0; i < 10; i++ {
		z = z - (z*z-x)/(2*z)
	}
	return z
}

func CosDeg(x float64) float64 {
	// Taylor series approximation for cosine
	x = math.Mod(x, 2*math.Pi)
	result := 1.0
	term := 1.0
	for i := 2; i <= 10; i += 2 {
		term = term * (-x * x / float64(i*(i-1)))
		result += term
	}
	return result
}

func AsinDeg(x float64) float64 {
	// Taylor series approximation for arcsine
	result := x
	term := x
	for i := 1; i <= 5; i++ {
		term = term * x * x * float64(2*i-1) * float64(2*i-1) / float64(2*i) / float64(2*i+1)
		result += term
	}
	return result
}

func MinDeg(a, b float64) float64 {
	if a < b {
		return a
	}
	return b
}
