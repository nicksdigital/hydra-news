package apitest

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"github.com/gorilla/mux"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/mock"

	"github.com/hydra-news/api"
	"github.com/hydra-news/keyvault"
)

// MockKeyVault mocks the KeyVault interface for testing
type MockKeyVault struct {
	mock.Mock
}

func (m *MockKeyVault) GetKey(keyName string) (interface{}, error) {
	args := m.Called(keyName)
	return args.Get(0), args.Error(1)
}

// TestAuthMiddleware tests the authentication middleware
func TestAuthMiddleware(t *testing.T) {
	// Create mock key vault
	mockVault := new(MockKeyVault)
	
	// Configure mock to return test keys
	mockVault.On("GetKey", "jwt_signing_key").Return([]byte("test_signing_key"), nil)
	mockVault.On("GetKey", "jwt_verification_key").Return([]byte("test_verification_key"), nil)
	
	// Create auth service
	authConfig := api.AuthConfig{
		TokenExpiryMinutes: 60,
		RateLimitRequests:  100,
		RateLimitWindow:    time.Duration(1) * time.Minute,
	}
	authService := api.NewAuthService(authConfig, mockVault)
	
	// Create test handler
	testHandler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("test_success"))
	})
	
	// Create test router with middleware
	router := mux.NewRouter()
	router.Use(authService.AuthMiddleware)
	router.HandleFunc("/test", testHandler).Methods("GET")
	router.HandleFunc("/api/v1/login", testHandler).Methods("GET") // Public endpoint
	
	// Test cases
	tests := []struct {
		name           string
		path           string
		method         string
		authHeader     string
		expectedStatus int
	}{
		{
			name:           "Public Endpoint No Auth",
			path:           "/api/v1/login",
			method:         "GET",
			authHeader:     "",
			expectedStatus: http.StatusOK,
		},
		{
			name:           "Protected Endpoint No Auth",
			path:           "/test",
			method:         "GET",
			authHeader:     "",
			expectedStatus: http.StatusUnauthorized,
		},
		{
			name:           "Protected Endpoint Invalid Auth Format",
			path:           "/test",
			method:         "GET",
			authHeader:     "InvalidFormat Token",
			expectedStatus: http.StatusUnauthorized,
		},
		// Additional test cases would be added for valid tokens,
		// rate limiting, etc.
	}
	
	// Run tests
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Create request
			req, err := http.NewRequest(tt.method, tt.path, nil)
			assert.NoError(t, err)
			
			if tt.authHeader != "" {
				req.Header.Set("Authorization", tt.authHeader)
			}
			
			// Create response recorder
			rr := httptest.NewRecorder()
			
			// Serve request
			router.ServeHTTP(rr, req)
			
			// Check status code
			assert.Equal(t, tt.expectedStatus, rr.Code)
		})
	}
}

// TestInputValidation tests the input validation middleware
func TestInputValidation(t *testing.T) {
	// Create validator
	validator := api.NewValidator(1024 * 1024) // 1MB max size
	
	// Create test schema type
	type TestSchema struct {
		Name  string `json:"name"`
		Email string `json:"email"`
		Age   int    `json:"age"`
	}
	
	// Implement Validatable interface for TestSchema
	func (s *TestSchema) Validate() error {
		errors := api.ValidationErrors{Errors: []api.ValidationError{}}
		
		if s.Name == "" {
			errors.Errors = append(errors.Errors, api.ValidationError{
				Field:   "name",
				Message: "Name is required",
			})
		}
		
		if s.Email == "" {
			errors.Errors = append(errors.Errors, api.ValidationError{
				Field:   "email",
				Message: "Email is required",
			})
		}
		
		if s.Age < 18 {
			errors.Errors = append(errors.Errors, api.ValidationError{
				Field:   "age",
				Message: "Age must be at least 18",
			})
		}
		
		if len(errors.Errors) > 0 {
			return errors
		}
		
		return nil
	}
	
	// Create test handler
	testHandler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("validation_success"))
	})
	
	// Create validation middleware
	validationMiddleware := validator.ValidationMiddleware(func() api.Validatable {
		return &TestSchema{}
	})
	
	// Create test router with middleware
	router := mux.NewRouter()
	router.Use(validator.InputValidationMiddleware)
	router.Handle("/test", validationMiddleware(testHandler)).Methods("POST")
	
	// Test cases
	tests := []struct {
		name           string
		contentType    string
		body           interface{}
		expectedStatus int
	}{
		{
			name:           "Invalid Content Type",
			contentType:    "text/plain",
			body:           `{"name": "Test", "email": "test@example.com", "age": 25}`,
			expectedStatus: http.StatusUnsupportedMediaType,
		},
		{
			name:           "Valid Request",
			contentType:    "application/json",
			body:           map[string]interface{}{"name": "Test", "email": "test@example.com", "age": 25},
			expectedStatus: http.StatusOK,
		},
		{
			name:           "Missing Required Field",
			contentType:    "application/json",
			body:           map[string]interface{}{"name": "Test", "age": 25},
			expectedStatus: http.StatusBadRequest,
		},
		{
			name:           "Invalid Field Value",
			contentType:    "application/json",
			body:           map[string]interface{}{"name": "Test", "email": "test@example.com", "age": 17},
			expectedStatus: http.StatusBadRequest,
		},
	}
	
	// Run tests
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Create request body
			var body []byte
			var err error
			
			if str, ok := tt.body.(string); ok {
				body = []byte(str)
			} else {
				body, err = json.Marshal(tt.body)
				assert.NoError(t, err)
			}
			
			// Create request
			req, err := http.NewRequest("POST", "/test", bytes.NewBuffer(body))
			assert.NoError(t, err)
			
			req.Header.Set("Content-Type", tt.contentType)
			
			// Create response recorder
			rr := httptest.NewRecorder()
			
			// Serve request
			router.ServeHTTP(rr, req)
			
			// Check status code
			assert.Equal(t, tt.expectedStatus, rr.Code)
		})
	}
}

// TestRateLimiter tests the rate limiter
func TestRateLimiter(t *testing.T) {
	// Create rate limiter with low limits for testing
	limiter := api.NewRateLimiter(3, time.Duration(1)*time.Second)
	
	// Test allowing requests under the limit
	for i := 0; i < 3; i++ {
		allowed := limiter.Allow("test_client")
		assert.True(t, allowed, "Request %d should be allowed", i+1)
	}
	
	// Test blocking requests over the limit
	allowed := limiter.Allow("test_client")
	assert.False(t, allowed, "Request 4 should be blocked")
	
	// Test allowing requests for different clients
	allowed = limiter.Allow("different_client")
	assert.True(t, allowed, "Request from different client should be allowed")
	
	// Test allowing requests after waiting
	time.Sleep(time.Duration(1) * time.Second)
	allowed = limiter.Allow("test_client")
	assert.True(t, allowed, "Request after waiting should be allowed")
}

// TestLogging tests the logging middleware
func TestLogging(t *testing.T) {
	// Create temporary log file
	logFile := "/tmp/test_api_log.json"
	
	// Create logger
	logger, err := api.NewLogger(logFile, "test_component")
	assert.NoError(t, err)
	defer logger.Close()
	
	// Create test handler
	testHandler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("logging_test"))
	})
	
	// Create test router with middleware
	router := mux.NewRouter()
	router.Use(logger.LoggingMiddleware)
	router.HandleFunc("/test", testHandler).Methods("GET")
	
	// Create request
	req, err := http.NewRequest("GET", "/test", nil)
	assert.NoError(t, err)
	
	// Add test headers
	req.Header.Set("User-Agent", "Test Agent")
	req.Header.Set("Referer", "http://test-referrer.com")
	
	// Create response recorder
	rr := httptest.NewRecorder()
	
	// Serve request
	router.ServeHTTP(rr, req)
	
	// Check status code
	assert.Equal(t, http.StatusOK, rr.Code)
	
	// Check if X-Request-ID was added to response
	requestID := rr.Header().Get("X-Request-ID")
	assert.NotEmpty(t, requestID)
}
