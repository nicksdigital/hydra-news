package api

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"time"

	"github.com/google/uuid"
)

// LogLevel defines logging severity levels
type LogLevel string

const (
	LogDebug   LogLevel = "DEBUG"
	LogInfo    LogLevel = "INFO"
	LogWarning LogLevel = "WARNING"
	LogError   LogLevel = "ERROR"
	LogFatal   LogLevel = "FATAL"
)

// LogEntry represents a structured log entry
type LogEntry struct {
	Timestamp   time.Time `json:"timestamp"`
	Level       LogLevel  `json:"level"`
	RequestID   string    `json:"request_id,omitempty"`
	UserID      string    `json:"user_id,omitempty"`
	IP          string    `json:"ip,omitempty"`
	Method      string    `json:"method,omitempty"`
	Path        string    `json:"path,omitempty"`
	Status      int       `json:"status,omitempty"`
	Duration    int64     `json:"duration_ms,omitempty"`
	Message     string    `json:"message"`
	Error       string    `json:"error,omitempty"`
	ContentType string    `json:"content_type,omitempty"`
	UserAgent   string    `json:"user_agent,omitempty"`
	Referrer    string    `json:"referrer,omitempty"`
	Component   string    `json:"component"`
	Action      string    `json:"action,omitempty"`
}

// Logger provides structured logging for the API
type Logger struct {
	logFile   *os.File
	component string
}

// NewLogger creates a new logger instance
func NewLogger(logPath, component string) (*Logger, error) {
	// Open or create log file
	logFile, err := os.OpenFile(logPath, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
	if err != nil {
		return nil, fmt.Errorf("failed to open log file: %w", err)
	}

	return &Logger{
		logFile:   logFile,
		component: component,
	}, nil
}

// Close closes the log file
func (l *Logger) Close() error {
	return l.logFile.Close()
}

// Log writes a log entry to the log file
func (l *Logger) Log(entry LogEntry) error {
	// Set component if not already set
	if entry.Component == "" {
		entry.Component = l.component
	}
	
	// Set timestamp if not already set
	if entry.Timestamp.IsZero() {
		entry.Timestamp = time.Now()
	}
	
	// Serialize entry to JSON
	entryJSON, err := json.Marshal(entry)
	if err != nil {
		return fmt.Errorf("failed to marshal log entry: %w", err)
	}
	
	// Write to log file
	if _, err := l.logFile.Write(append(entryJSON, '\n')); err != nil {
		return fmt.Errorf("failed to write log entry: %w", err)
	}
	
	return nil
}

// LogInfo logs an info-level message
func (l *Logger) LogInfo(ctx context.Context, message string, action string) {
	requestID, _ := ctx.Value("requestID").(string)
	userID, _ := ctx.Value("userID").(string)
	
	l.Log(LogEntry{
		Level:     LogInfo,
		RequestID: requestID,
		UserID:    userID,
		Message:   message,
		Action:    action,
	})
}

// LogError logs an error-level message
func (l *Logger) LogError(ctx context.Context, message string, err error, action string) {
	requestID, _ := ctx.Value("requestID").(string)
	userID, _ := ctx.Value("userID").(string)
	
	errStr := ""
	if err != nil {
		errStr = err.Error()
	}
	
	l.Log(LogEntry{
		Level:     LogError,
		RequestID: requestID,
		UserID:    userID,
		Message:   message,
		Error:     errStr,
		Action:    action,
	})
}

// LoggingMiddleware adds request logging
func (l *Logger) LoggingMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()
		
		// Generate request ID
		requestID := uuid.New().String()
		
		// Create response writer that captures status code
		rw := newResponseWriter(w)
		
		// Add request ID to context
		ctx := context.WithValue(r.Context(), "requestID", requestID)
		
		// Add request ID to response headers
		rw.Header().Set("X-Request-ID", requestID)
		
		// Process request
		next.ServeHTTP(rw, r.WithContext(ctx))
		
		// Calculate request duration
		duration := time.Since(start)
		
		// Get user ID from context if available
		userID, _ := ctx.Value("userID").(string)
		
		// Log request
		l.Log(LogEntry{
			Level:       LogInfo,
			RequestID:   requestID,
			UserID:      userID,
			IP:          getClientIP(r),
			Method:      r.Method,
			Path:        r.URL.Path,
			Status:      rw.status,
			Duration:    duration.Milliseconds(),
			ContentType: r.Header.Get("Content-Type"),
			UserAgent:   r.UserAgent(),
			Referrer:    r.Referer(),
			Action:      "http_request",
		})
	})
}

// responseWriter is a wrapper for http.ResponseWriter that captures the status code
type responseWriter struct {
	http.ResponseWriter
	status      int
	wroteHeader bool
}

// newResponseWriter creates a new responseWriter
func newResponseWriter(w http.ResponseWriter) *responseWriter {
	return &responseWriter{
		ResponseWriter: w,
		status:         http.StatusOK,
	}
}

// WriteHeader captures the status code and calls the wrapped ResponseWriter's WriteHeader
func (rw *responseWriter) WriteHeader(code int) {
	if !rw.wroteHeader {
		rw.status = code
		rw.wroteHeader = true
		rw.ResponseWriter.WriteHeader(code)
	}
}

// Write captures that headers have been written and calls the wrapped ResponseWriter's Write
func (rw *responseWriter) Write(b []byte) (int, error) {
	if !rw.wroteHeader {
		rw.WriteHeader(http.StatusOK)
	}
	return rw.ResponseWriter.Write(b)
}

// Helper functions for specific log events

// logRateLimitExceeded logs a rate limit exceeded event
func logRateLimitExceeded(clientIP, path string) {
	// Implementation depends on the global logger setup
	// This would be implemented in the main server file
}

// logUnauthorizedAccess logs an unauthorized access attempt
func logUnauthorizedAccess(r *http.Request, reason string) {
	// Implementation depends on the global logger setup
	// This would be implemented in the main server file
}

// logValidationError logs a validation error
func logValidationError(r *http.Request, details string) {
	// Implementation depends on the global logger setup
	// This would be implemented in the main server file
}

// addClaimsToContext adds authentication claims to the request context
func addClaimsToContext(ctx context.Context, claims *TokenClaims) context.Context {
	// Add user ID to context
	ctx = context.WithValue(ctx, "userID", claims.UserID)
	
	// Add user roles to context
	ctx = context.WithValue(ctx, "userRoles", claims.UserRoles)
	
	return ctx
}

// addValidatedSchemaToContext adds validated request schema to the context
func addValidatedSchemaToContext(ctx context.Context, schema interface{}) context.Context {
	return context.WithValue(ctx, "validatedSchema", schema)
}
