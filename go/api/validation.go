package api

import (
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"regexp"
	"strings"
)

// ValidationError represents an input validation error
type ValidationError struct {
	Field   string `json:"field"`
	Message string `json:"message"`
}

// ValidationErrors holds multiple validation errors
type ValidationErrors struct {
	Errors []ValidationError `json:"errors"`
}

// Error implements the error interface
func (ve ValidationErrors) Error() string {
	if len(ve.Errors) == 0 {
		return "validation failed"
	}
	
	messages := make([]string, len(ve.Errors))
	for i, err := range ve.Errors {
		messages[i] = fmt.Sprintf("%s: %s", err.Field, err.Message)
	}
	
	return strings.Join(messages, "; ")
}

// Validator provides input validation
type Validator struct {
	// Regex patterns for common validations
	emailPattern    *regexp.Regexp
	urlPattern      *regexp.Regexp
	usernamePattern *regexp.Regexp
	maxJSONSize     int64
}

// NewValidator creates a new validator
func NewValidator(maxJSONSize int64) *Validator {
	return &Validator{
		emailPattern:    regexp.MustCompile(`^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$`),
		urlPattern:      regexp.MustCompile(`^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$`),
		usernamePattern: regexp.MustCompile(`^[a-zA-Z0-9_\-\.]{3,32}$`),
		maxJSONSize:     maxJSONSize,
	}
}

// ValidateAndDecode validates and decodes JSON request body
func (v *Validator) ValidateAndDecode(r *http.Request, schema interface{}) error {
	// Limit request body size to prevent DoS attacks
	r.Body = http.MaxBytesReader(nil, r.Body, v.maxJSONSize)
	
	decoder := json.NewDecoder(r.Body)
	decoder.DisallowUnknownFields()
	
	if err := decoder.Decode(schema); err != nil {
		var syntaxErr *json.SyntaxError
		var unmarshalTypeErr *json.UnmarshalTypeError
		var invalidUnmarshalErr *json.InvalidUnmarshalError
		
		switch {
		case errors.As(err, &syntaxErr):
			return fmt.Errorf("malformed JSON at position %d", syntaxErr.Offset)
		
		case errors.As(err, &unmarshalTypeErr):
			return fmt.Errorf("invalid value for field %q at position %d", 
				unmarshalTypeErr.Field, unmarshalTypeErr.Offset)
		
		case errors.As(err, &invalidUnmarshalErr):
			return fmt.Errorf("invalid unmarshal error: %w", err)
		
		case strings.HasPrefix(err.Error(), "json: unknown field"):
			fieldName := strings.TrimPrefix(err.Error(), "json: unknown field ")
			return fmt.Errorf("unknown field %s", fieldName)
		
		case errors.Is(err, io.EOF):
			return errors.New("request body must not be empty")
		
		case err.Error() == "http: request body too large":
			return fmt.Errorf("request body must not be larger than %d bytes", v.maxJSONSize)
		
		default:
			return fmt.Errorf("failed to decode JSON: %w", err)
		}
	}
	
	// Check for additional JSON data
	if decoder.More() {
		return errors.New("request body must only contain a single JSON object")
	}
	
	// Perform schema-specific validation
	if validator, ok := schema.(Validatable); ok {
		return validator.Validate()
	}
	
	return nil
}

// Validatable interface for types that can validate themselves
type Validatable interface {
	Validate() error
}

// Common validation functions

// ValidateEmail validates email format
func (v *Validator) ValidateEmail(email string) bool {
	return v.emailPattern.MatchString(email)
}

// ValidateURL validates URL format
func (v *Validator) ValidateURL(url string) bool {
	return v.urlPattern.MatchString(url)
}

// ValidateUsername validates username format
func (v *Validator) ValidateUsername(username string) bool {
	return v.usernamePattern.MatchString(username)
}

// ValidateLength validates string length
func (v *Validator) ValidateLength(str string, min, max int) bool {
	length := len(str)
	return length >= min && length <= max
}

// ValidateRange validates integer range
func (v *Validator) ValidateRange(value, min, max int) bool {
	return value >= min && value <= max
}

// ValidateEnum validates that a value is in a set of allowed values
func (v *Validator) ValidateEnum(value string, allowedValues []string) bool {
	for _, allowed := range allowedValues {
		if value == allowed {
			return true
		}
	}
	return false
}

// InputValidationMiddleware adds input validation to handlers
func (v *Validator) InputValidationMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Validate content type for POST/PUT/PATCH requests
		if r.Method == http.MethodPost || r.Method == http.MethodPut || r.Method == http.MethodPatch {
			contentType := r.Header.Get("Content-Type")
			
			if contentType != "application/json" {
				http.Error(w, "Content-Type must be application/json", http.StatusUnsupportedMediaType)
				logValidationError(r, "invalid_content_type")
				return
			}
		}
		
		// Continue to next handler
		next.ServeHTTP(w, r)
	})
}

// ValidationMiddleware creates middleware for a specific validation schema
func (v *Validator) ValidationMiddleware(schemaFactory func() Validatable) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			// Only validate POST/PUT/PATCH requests
			if r.Method == http.MethodPost || r.Method == http.MethodPut || r.Method == http.MethodPatch {
				schema := schemaFactory()
				
				if err := v.ValidateAndDecode(r, schema); err != nil {
					w.Header().Set("Content-Type", "application/json")
					w.WriteHeader(http.StatusBadRequest)
					
					var valErrors ValidationErrors
					if errors.As(err, &valErrors) {
						json.NewEncoder(w).Encode(valErrors)
					} else {
						json.NewEncoder(w).Encode(map[string]string{"error": err.Error()})
					}
					
					logValidationError(r, err.Error())
					return
				}
				
				// Add validated schema to request context
				ctx := addValidatedSchemaToContext(r.Context(), schema)
				r = r.WithContext(ctx)
			}
			
			next.ServeHTTP(w, r)
		})
	}
}
