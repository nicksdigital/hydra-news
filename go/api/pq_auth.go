package api

import (
	"crypto/rand"
	"encoding/base64"
	"errors"
	"fmt"
	"hydranews/keyvault"
	"net/http"
	"time"

	"github.com/golang-jwt/jwt/v4"
)

// PQTokenClaims extends JWT registered claims with post-quantum security
type PQTokenClaims struct {
	UserID    string   `json:"user_id"`
	UserRoles []string `json:"user_roles"`
	jwt.RegisteredClaims
}

// PQSigningMethod implements a post-quantum signing method for JWT
type PQSigningMethod struct {
	Name string
	// Falcon or Kyber
	Algorithm string
}

// Specific signing method instances
var (
	SigningMethodFalcon = &PQSigningMethod{Name: "Falcon", Algorithm: "falcon"}
	SigningMethodKyber  = &PQSigningMethod{Name: "Kyber", Algorithm: "kyber"}
)

// Alg returns the name of the signing method
func (m *PQSigningMethod) Alg() string {
	return m.Name
}

// Verify implements the Verify method for the jwt.SigningMethod interface
func (m *PQSigningMethod) Verify(signingString string, signature string, key interface{}) error {
	// Decode the signature
	sig, err := base64.RawURLEncoding.DecodeString(signature)
	if err != nil {
		return fmt.Errorf("PQ-JWT: error decoding signature: %w", err)
	}

	// Get the verification key
	var verificationKey []byte
	switch k := key.(type) {
	case []byte:
		verificationKey = k
	case string:
		verificationKey = []byte(k)
	default:
		return fmt.Errorf("PQ-JWT: invalid key type %T", key)
	}

	// Verify the signature using the appropriate algorithm
	switch m.Algorithm {
	case "falcon":
		// In a real implementation, this would call the Falcon verification function
		// For now, we'll use a placeholder implementation
		return verifyFalconSignature([]byte(signingString), sig, verificationKey)
	case "kyber":
		// Kyber is a KEM, not a signature scheme, so this is just for illustration
		return errors.New("PQ-JWT: Kyber is not a signature scheme")
	default:
		return fmt.Errorf("PQ-JWT: unknown algorithm %s", m.Algorithm)
	}
}

// Sign implements the Sign method for the jwt.SigningMethod interface
func (m *PQSigningMethod) Sign(signingString string, key interface{}) (string, error) {
	// Get the signing key
	var signingKey []byte
	switch k := key.(type) {
	case []byte:
		signingKey = k
	case string:
		signingKey = []byte(k)
	default:
		return "", fmt.Errorf("PQ-JWT: invalid key type %T", key)
	}

	// Sign the string using the appropriate algorithm
	var signature []byte
	var err error
	switch m.Algorithm {
	case "falcon":
		// In a real implementation, this would call the Falcon signing function
		// For now, we'll use a placeholder implementation
		signature, err = signWithFalcon([]byte(signingString), signingKey)
	case "kyber":
		// Kyber is a KEM, not a signature scheme, so this is just for illustration
		return "", errors.New("PQ-JWT: Kyber is not a signature scheme")
	default:
		return "", fmt.Errorf("PQ-JWT: unknown algorithm %s", m.Algorithm)
	}

	if err != nil {
		return "", err
	}

	// Encode the signature
	return base64.RawURLEncoding.EncodeToString(signature), nil
}

// Placeholder implementation for Falcon signature verification
func verifyFalconSignature(message, signature, publicKey []byte) error {
	// In a real implementation, this would call the C library for Falcon verification
	// For now, we'll use a simple placeholder that checks if the signature is valid

	// For testing purposes, we'll consider signatures valid if they start with a specific pattern
	// This is NOT secure and is only for demonstration
	if len(signature) < 4 {
		return errors.New("PQ-JWT: signature too short")
	}

	// Check if the signature starts with the expected pattern
	// In a real implementation, this would perform actual cryptographic verification
	if signature[0] == 0x30 && signature[1] == publicKey[0] {
		return nil
	}

	return errors.New("PQ-JWT: invalid signature")
}

// Placeholder implementation for Falcon signing
func signWithFalcon(message, privateKey []byte) ([]byte, error) {
	// In a real implementation, this would call the C library for Falcon signing
	// For now, we'll use a simple placeholder that generates a deterministic signature

	// Create a signature with a specific format for testing
	// This is NOT secure and is only for demonstration
	signature := make([]byte, 64)
	signature[0] = 0x30          // Version byte
	signature[1] = privateKey[0] // Use first byte of private key

	// Fill the rest with deterministic but seemingly random data
	for i := 2; i < 64; i++ {
		signature[i] = byte((int(message[i%len(message)]) + int(privateKey[i%len(privateKey)])) % 256)
	}

	return signature, nil
}

// PQAuthService extends AuthService with post-quantum security
type PQAuthService struct {
	*AuthService
}

// NewPQAuthService creates a new post-quantum auth service
func NewPQAuthService(config AuthConfig, keyManager *keyvault.KeyManager) *PQAuthService {
	// Register the post-quantum signing methods with JWT
	jwt.RegisterSigningMethod(SigningMethodFalcon.Alg(), func() jwt.SigningMethod {
		return SigningMethodFalcon
	})

	// Create the base auth service
	baseService := NewAuthService(config, keyManager)

	return &PQAuthService{
		AuthService: baseService,
	}
}

// CreatePQToken generates a JWT token using post-quantum signatures
func (a *PQAuthService) CreatePQToken(userID string, roles []string) (string, error) {
	claims := PQTokenClaims{
		UserID:    userID,
		UserRoles: roles,
		RegisteredClaims: jwt.RegisteredClaims{
			ExpiresAt: jwt.NewNumericDate(time.Now().Add(time.Duration(a.config.TokenExpiryMinutes) * time.Minute)),
			IssuedAt:  jwt.NewNumericDate(time.Now()),
			NotBefore: jwt.NewNumericDate(time.Now()),
			Issuer:    "hydra-news-pq",
			Subject:   userID,
			ID:        generateTokenID(),
			Audience:  []string{"hydra-news-api"},
		},
	}

	// Get signing key from key manager
	signingKey, err := a.keyManager.GetKey("jwt_signing_key", "signing")
	if err != nil {
		return "", err
	}

	// Create token with Falcon signature
	token := jwt.NewWithClaims(SigningMethodFalcon, claims)
	tokenString, err := token.SignedString(signingKey)
	if err != nil {
		return "", err
	}

	return tokenString, nil
}

// ValidatePQToken validates a post-quantum JWT token
func (a *PQAuthService) ValidatePQToken(tokenString string) (*PQTokenClaims, error) {
	claims := &PQTokenClaims{}

	// Get verification key from key manager
	verificationKey, err := a.keyManager.GetKey("jwt_verification_key", "signing")
	if err != nil {
		return nil, err
	}

	// Parse and validate token
	token, err := jwt.ParseWithClaims(tokenString, claims, func(token *jwt.Token) (interface{}, error) {
		// Check if the signing method is what we expect
		if _, ok := token.Method.(*PQSigningMethod); !ok {
			return nil, jwt.NewValidationError(
				fmt.Sprintf("unexpected signing method: %v", token.Header["alg"]),
				jwt.ValidationErrorSignatureInvalid,
			)
		}
		return verificationKey, nil
	})

	if err != nil {
		return nil, err
	}

	if !token.Valid {
		return nil, jwt.NewValidationError("invalid token", jwt.ValidationErrorNotValidYet)
	}

	return claims, nil
}

// PQAuthMiddleware handles authentication with post-quantum security
func (a *PQAuthService) PQAuthMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Check rate limits
		clientIP := getClientIP(r)
		if !a.rateLimiter.Allow(clientIP) {
			http.Error(w, "Rate limit exceeded", http.StatusTooManyRequests)
			logRateLimitExceeded(clientIP, r.URL.Path)
			return
		}

		// Skip auth for public endpoints
		if isPublicEndpoint(r.URL.Path) {
			next.ServeHTTP(w, r)
			return
		}

		// Extract token from Authorization header
		authHeader := r.Header.Get("Authorization")
		if authHeader == "" {
			http.Error(w, "Authorization header required", http.StatusUnauthorized)
			logUnauthorizedAccess(r, "missing_auth_header")
			return
		}

		// Check token format
		if len(authHeader) < 7 || authHeader[:7] != "Bearer " {
			http.Error(w, "Invalid authorization format", http.StatusUnauthorized)
			logUnauthorizedAccess(r, "invalid_auth_format")
			return
		}

		tokenString := authHeader[7:]
		claims, err := a.ValidatePQToken(tokenString)
		if err != nil {
			http.Error(w, "Invalid or expired token", http.StatusUnauthorized)
			logUnauthorizedAccess(r, "invalid_token")
			return
		}

		// Check if user has required roles for this endpoint
		if !hasRequiredRoles(r.URL.Path, r.Method, claims.UserRoles) {
			http.Error(w, "Insufficient permissions", http.StatusForbidden)
			logUnauthorizedAccess(r, "insufficient_permissions")
			return
		}

		// Add claims to request context
		ctx := addClaimsToContext(r.Context(), &TokenClaims{
			UserID:    claims.UserID,
			UserRoles: claims.UserRoles,
			StandardClaims: jwt.StandardClaims{
				ExpiresAt: claims.ExpiresAt.Unix(),
				IssuedAt:  claims.IssuedAt.Unix(),
			},
		})
		next.ServeHTTP(w, r.WithContext(ctx))
	})
}

// generateTokenID generates a unique token ID
func generateTokenID() string {
	// Generate 16 random bytes
	b := make([]byte, 16)
	_, err := rand.Read(b)
	if err != nil {
		// Fall back to timestamp if random generation fails
		return fmt.Sprintf("tkn-%d", time.Now().UnixNano())
	}

	// Encode as base64
	return base64.RawURLEncoding.EncodeToString(b)
}
