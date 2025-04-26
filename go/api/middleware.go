package api

import (
	"context"
	"net/http"
	"strconv"
	"time"
)

// Middleware represents a middleware function
type Middleware func(http.Handler) http.Handler

// Chain applies multiple middleware to a handler
func Chain(h http.Handler, middleware ...Middleware) http.Handler {
	for i := len(middleware) - 1; i >= 0; i-- {
		h = middleware[i](h)
	}
	return h
}

// RateLimitMiddleware creates a middleware that applies rate limiting
func RateLimitMiddleware(rateLimiter *RateLimiter, logger *Logger) Middleware {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			// Get client identifier (IP address)
			clientID := getClientIP(r)

			// Check if request is allowed
			if !rateLimiter.Allow(clientID) {
				// Log rate limit exceeded
				logger.Log(LogEntry{
					Level:     LogWarning,
					Message:   "Rate limit exceeded",
					IP:        clientID,
					Path:      r.URL.Path,
					Method:    r.Method,
					Action:    "rate_limit_exceeded",
					Timestamp: time.Now(),
				})

				// Return 429 Too Many Requests
				w.Header().Set("Content-Type", "application/json")
				w.Header().Set("Retry-After", "60") // Suggest retry after 60 seconds
				w.WriteHeader(http.StatusTooManyRequests)
				w.Write([]byte(`{"error":"Rate limit exceeded. Please try again later."}`))
				return
			}

			// Continue to next handler
			next.ServeHTTP(w, r)
		})
	}
}

// This function is already defined in logging.go
// Keeping this comment as a reference

// ContextMiddleware adds common values to the request context
func ContextMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Generate request ID if not already present
		ctx := r.Context()
		if _, ok := ctx.Value("requestID").(string); !ok {
			requestID := generateRequestID()
			ctx = context.WithValue(ctx, "requestID", requestID)
			// Add request ID to response headers
			w.Header().Set("X-Request-ID", requestID)
		}

		// Continue with the updated context
		next.ServeHTTP(w, r.WithContext(ctx))
	})
}

// generateRequestID creates a unique request ID
func generateRequestID() string {
	// In a real implementation, this would use a UUID library
	// For simplicity, we'll use a timestamp-based ID
	return "req-" + generateTimestampID()
}

// generateTimestampID creates a timestamp-based ID
func generateTimestampID() string {
	// In a real implementation, this would use a UUID library
	// For simplicity, we'll use a timestamp-based ID
	ts := time.Now().UnixNano()
	tsstr := strconv.Itoa(int(ts))
	return "ts-" + tsstr
}
