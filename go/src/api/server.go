// Package api implements the server for Hydra News API
package api

import (
	"context"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/gorilla/mux"
	"github.com/rs/cors"
)

// Server represents the API server
type Server struct {
	router     *mux.Router
	httpServer *http.Server
	handler    *Handler
}

// NewServer creates a new API server
func NewServer(handler *Handler, port string) *Server {
	r := mux.NewRouter()
	
	// Set up routes
	handler.SetupRoutes(r)
	
	// Set up CORS
	corsMiddleware := cors.New(cors.Options{
		AllowedOrigins:   []string{"*"}, // In production, you would restrict this
		AllowedMethods:   []string{"GET", "POST", "PUT", "DELETE", "OPTIONS"},
		AllowedHeaders:   []string{"Content-Type", "Authorization"},
		AllowCredentials: true,
		MaxAge:           86400, // 24 hours
	})
	
	// Create HTTP server
	httpServer := &http.Server{
		Addr:    ":" + port,
		Handler: corsMiddleware.Handler(r),
	}
	
	return &Server{
		router:     r,
		httpServer: httpServer,
		handler:    handler,
	}
}

// Start starts the API server
func (s *Server) Start() error {
	// Channel for server errors
	errChan := make(chan error, 1)
	
	// Start server in a goroutine
	go func() {
		log.Printf("Starting server on port %s", s.httpServer.Addr)
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
		return err
	case <-stop:
		log.Println("Shutting down server...")
		
		// Create shutdown context with timeout
		ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
		defer cancel()
		
		// Shutdown the server gracefully
		if err := s.httpServer.Shutdown(ctx); err != nil {
			return err
		}
		
		log.Println("Server stopped gracefully")
	}
	
	return nil
}

// Stop stops the API server
func (s *Server) Stop() error {
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	
	return s.httpServer.Shutdown(ctx)
}
