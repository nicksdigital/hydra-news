// Package api implements the server for Hydra News API
package api

import (
	"context"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"hydranews/keyvault"
)

// ServerConfig holds server configuration
type ServerConfig struct {
	Port                string
	LogPath             string
	MaxRequestBodySize  int64
	RateLimitRequests   int
	RateLimitWindowSecs int
	TokenExpiryMinutes  int
}

// Server represents the API server
type Server struct {
	handler     *Handler
	keyManager  *keyvault.KeyManager
	config      ServerConfig
	logger      *Logger
	httpServer  *http.Server
	rateLimiter *RateLimiter
}

func NewServer(handler *Handler, keyManager *keyvault.KeyManager, config ServerConfig, logger *Logger, rateLimiter *RateLimiter) (*Server, error) {
	// Create post-quantum auth service
	authConfig := AuthConfig{
		TokenExpiryMinutes: config.TokenExpiryMinutes,
		RateLimitRequests:  config.RateLimitRequests,
		RateLimitWindow:    time.Duration(config.RateLimitWindowSecs) * time.Second,
	}
	pqAuthService := NewPQAuthService(authConfig, keyManager)

	// Apply middleware to handler
	wrappedHandler := Chain(handler,
		ContextMiddleware,                        // Add context values
		logger.LoggingMiddleware,                 // Log all requests
		RateLimitMiddleware(rateLimiter, logger), // Apply rate limiting
		pqAuthService.PQAuthMiddleware,           // Post-quantum authentication
	)

	httpSrv := &http.Server{
		Addr:    ":" + config.Port,
		Handler: wrappedHandler,
	}

	return &Server{
		handler:     handler,
		keyManager:  keyManager,
		config:      config,
		logger:      logger,
		httpServer:  httpSrv,
		rateLimiter: rateLimiter,
	}, nil
}

// Start starts the API server
func (s *Server) Start() error {
	// Channel for server errors
	errChan := make(chan error, 1)

	// Start server in a goroutine
	go func() {
		s.logger.LogInfo(context.Background(), "Starting server on port "+s.config.Port, "server_start")
		if err := s.httpServer.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			errChan <- err
		}
	}()

	// Channel for shutdown signals
	stop := make(chan os.Signal, 1)
	signal.Notify(stop, os.Interrupt, syscall.SIGTERM)

	// Wait for shutdown signal or error
	select {
	case err := <-errChan:
		s.logger.LogError(context.Background(), "Server error", err, "server_error")
		return err
	case <-stop:
		s.logger.LogInfo(context.Background(), "Shutting down server...", "server_shutdown")

		// Create shutdown context with timeout
		ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
		defer cancel()

		// Shutdown the server gracefully
		if err := s.httpServer.Shutdown(ctx); err != nil {
			s.logger.LogError(ctx, "Error during server shutdown", err, "server_shutdown_error")
			return err
		}

		s.logger.LogInfo(context.Background(), "Server stopped gracefully", "server_stopped")
	}

	return nil
}

// Stop stops the API server
func (s *Server) Stop() error {
	// Create shutdown context with timeout
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	// Log shutdown
	s.logger.LogInfo(ctx, "Stopping server...", "server_stop")

	// Stop rate limiter to prevent goroutine leak
	s.rateLimiter.Stop()

	// Close logger
	defer s.logger.Close()

	// Shutdown the server
	return s.httpServer.Shutdown(ctx)
}
