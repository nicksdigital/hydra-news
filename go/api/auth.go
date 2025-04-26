package api

import (
	"net/http"
	"sync"
	"time"

	"hydranews/keyvault"

	"github.com/golang-jwt/jwt/v4"
)

// TokenClaims extends JWT standard claims
type TokenClaims struct {
	UserID    string   `json:"user_id"`
	UserRoles []string `json:"user_roles"`
	jwt.StandardClaims
}

// AuthConfig stores auth configuration
type AuthConfig struct {
	TokenExpiryMinutes int
	RateLimitRequests  int
	RateLimitWindow    time.Duration
}

// AuthService handles authentication and rate limiting
// Use KeyManager instead of VaultClient
type AuthService struct {
	config      AuthConfig
	keyManager  *keyvault.KeyManager
	rateLimiter *RateLimiter
	mutex       sync.RWMutex
}

// NewAuthService creates new auth service
func NewAuthService(config AuthConfig, keyManager *keyvault.KeyManager) *AuthService {
	return &AuthService{
		config:      config,
		keyManager:  keyManager,
		rateLimiter: NewRateLimiter(config.RateLimitRequests, config.RateLimitWindow),
	}
}

// CreateToken generates a JWT token using post-quantum signatures
func (a *AuthService) CreateToken(userID string, roles []string) (string, error) {
	claims := TokenClaims{
		UserID:    userID,
		UserRoles: roles,
		StandardClaims: jwt.StandardClaims{
			ExpiresAt: time.Now().Add(time.Duration(a.config.TokenExpiryMinutes) * time.Minute).Unix(),
			IssuedAt:  time.Now().Unix(),
		},
	}

	// Get signing key from key manager
	signingKey, err := a.keyManager.GetKey("jwt_signing_key", "signing")
	if err != nil {
		return "", err
	}

	// TODO: Use Falcon signatures when available. For now, use HS256 for compatibility.
	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	tokenString, err := token.SignedString(signingKey)
	if err != nil {
		return "", err
	}

	return tokenString, nil
}

// ValidateToken validates the JWT token
func (a *AuthService) ValidateToken(tokenString string) (*TokenClaims, error) {
	claims := &TokenClaims{}

	// Get verification key from key manager
	verificationKey, err := a.keyManager.GetKey("jwt_verification_key", "signing")
	if err != nil {
		return nil, err
	}

	// Parse and validate token
	token, err := jwt.ParseWithClaims(tokenString, claims, func(token *jwt.Token) (interface{}, error) {
		// TODO: Use Falcon signing method check when available. For now, check for HS256.
		if _, ok := token.Method.(*jwt.SigningMethodHMAC); !ok {
			return nil, jwt.NewValidationError("unexpected signing method", jwt.ValidationErrorSignatureInvalid)
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

// AuthMiddleware handles authentication and rate limiting
func (a *AuthService) AuthMiddleware(next http.Handler) http.Handler {
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
		claims, err := a.ValidateToken(tokenString)
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
		ctx := addClaimsToContext(r.Context(), claims)
		next.ServeHTTP(w, r.WithContext(ctx))
	})
}

// Private helper functions
func isPublicEndpoint(path string) bool {
	publicEndpoints := []string{
		"/api/v1/login",
		"/api/v1/register",
		"/api/v1/health",
		"/api/v1/public/news",
	}

	for _, endpoint := range publicEndpoints {
		if path == endpoint {
			return true
		}
	}
	return false
}

func hasRequiredRoles(path string, method string, userRoles []string) bool {
	// Implement role-based access control logic here
	endpointRoles := getRequiredRolesForEndpoint(path, method)

	// Check if user has any of the required roles
	for _, requiredRole := range endpointRoles {
		for _, userRole := range userRoles {
			if requiredRole == userRole {
				return true
			}
		}
	}

	return len(endpointRoles) == 0 // Allow if no specific roles required
}

func getRequiredRolesForEndpoint(path string, method string) []string {
	// Define role requirements for different endpoints
	// This is a simple implementation - in production, this would likely be
	// stored in a database or configuration file

	roleMap := map[string]map[string][]string{
		"/api/v1/admin/users": {
			"GET":    {"admin"},
			"POST":   {"admin"},
			"PUT":    {"admin"},
			"DELETE": {"admin"},
		},
		"/api/v1/articles": {
			"POST":   {"editor", "journalist"},
			"PUT":    {"editor", "journalist"},
			"DELETE": {"editor", "admin"},
		},
		"/api/v1/verification": {
			"POST": {"verifier", "editor"},
		},
	}

	if methodRoles, ok := roleMap[path]; ok {
		if roles, ok := methodRoles[method]; ok {
			return roles
		}
	}

	return []string{}
}

func getClientIP(r *http.Request) string {
	// Try to get IP from X-Forwarded-For header
	ip := r.Header.Get("X-Forwarded-For")
	if ip != "" {
		return ip
	}

	// Fall back to RemoteAddr
	return r.RemoteAddr
}
