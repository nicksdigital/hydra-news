// Package api implements the RESTful API for Hydra News
package api

import (
	"crypto/sha256"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"strings"
	"time"

	"github.com/gorilla/mux"

	"hydranews/consensus"
	"hydranews/identity"
)

// ContentRequest represents the request body for content submission
type ContentRequest struct {
	Title   string `json:"title"`
	Content string `json:"content"`
	Source  string `json:"source"`
	Author  string `json:"author,omitempty"`
	URL     string `json:"url,omitempty"`
}

// ContentResponse represents the response for content operations
type ContentResponse struct {
	Title             string                   `json:"title"`
	Content           string                   `json:"content"`
	Source            string                   `json:"source"`
	Author            string                   `json:"author,omitempty"`
	URL               string                   `json:"url,omitempty"`
	ContentHash       string                   `json:"content_hash"`
	EntanglementHash  string                   `json:"entanglement_hash,omitempty"`
	ProcessedAt       time.Time                `json:"processed_at"`
	Processed         bool                     `json:"processed"`
	Entities          []map[string]interface{} `json:"entities,omitempty"`
	Claims            []map[string]interface{} `json:"claims,omitempty"`
	VerificationLevel int                      `json:"verification_level,omitempty"`
}

// VerificationRequest represents the request for content verification
type VerificationRequest struct {
	ContentHash   string   `json:"content_hash"`
	ReferenceURLs []string `json:"reference_urls,omitempty"`
}

// VerificationResponse represents the verification result
type VerificationResponse struct {
	ContentHash       string                   `json:"content_hash"`
	VerificationScore float64                  `json:"verification_score"`
	VerifiedClaims    []map[string]interface{} `json:"verified_claims"`
	DisputedClaims    []map[string]interface{} `json:"disputed_claims"`
	References        []map[string]interface{} `json:"references"`
	Timestamp         time.Time                `json:"timestamp"`
}

// SystemStatusResponse represents the system status information
type SystemStatusResponse struct {
	ActiveNodes             int     `json:"activeNodes"`
	VerifiedContent         int     `json:"verifiedContent"`
	AverageVerificationTime float64 `json:"averageVerificationTime"`
	SystemHealth            string  `json:"systemHealth"`
}

// Handler holds dependencies for API handlers
type Handler struct {
	ConsensusNetwork *consensus.ConsensusNetwork
	IdentityService  *identity.IdentityService
	ContentProcessor ContentProcessor
	AuthService      *PQAuthService
}

// ContentProcessor interface for processing content
type ContentProcessor interface {
	ProcessContent(title, content, source, author, url string) (string, string, []map[string]interface{}, []map[string]interface{}, error)
	ExtractFromURL(url string) (string, string, string, string, error)
	VerifyContent(contentHash string, referenceURLs []string) (*VerificationResponse, error)
}

// NewHandler creates a new API handler instance
func NewHandler(consensusNetwork *consensus.ConsensusNetwork, identityService *identity.IdentityService, contentProcessor ContentProcessor, authService *PQAuthService) *Handler {
	return &Handler{
		ConsensusNetwork: consensusNetwork,
		IdentityService:  identityService,
		ContentProcessor: contentProcessor,
		AuthService:      authService,
	}
}

// SetupRoutes configures the routes for the API
func (h *Handler) SetupRoutes(r *mux.Router) {
	// Authentication Endpoints
	r.HandleFunc("/api/v1/login", h.Login).Methods("POST")
	r.HandleFunc("/api/v1/register", h.Register).Methods("POST")

	// Content Endpoints
	r.HandleFunc("/api/content/submit", h.SubmitContent).Methods("POST")
	r.HandleFunc("/api/content/extract", h.ExtractContentFromURL).Methods("POST")
	r.HandleFunc("/api/content/verify", h.VerifyContent).Methods("POST")
	r.HandleFunc("/api/content", h.GetRecentContent).Methods("GET")
	r.HandleFunc("/api/content/{hash}", h.GetContent).Methods("GET")
	r.HandleFunc("/api/content/search", h.SearchContent).Methods("GET")
	r.HandleFunc("/api/content/cross-reference", h.CrossReferenceContent).Methods("POST")

	// Verification Endpoints
	r.HandleFunc("/api/verification/{hash}", h.GetVerification).Methods("GET")

	// System Status Endpoint
	r.HandleFunc("/api/system/status", h.GetSystemStatus).Methods("GET")

	// Sources Endpoint
	r.HandleFunc("/api/sources/trust-score/{source}", h.GetSourceTrustScore).Methods("GET")
}

// SubmitContent processes and stores new content
func (h *Handler) SubmitContent(w http.ResponseWriter, r *http.Request) {
	var req ContentRequest

	// Parse request body
	err := json.NewDecoder(r.Body).Decode(&req)
	if err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	// Validate request
	if req.Title == "" || req.Content == "" || req.Source == "" {
		http.Error(w, "Title, content, and source are required", http.StatusBadRequest)
		return
	}

	// Process content
	contentHash, entanglementHash, entities, claims, err := h.ContentProcessor.ProcessContent(
		req.Title, req.Content, req.Source, req.Author, req.URL,
	)
	if err != nil {
		log.Printf("Error processing content: %v", err)
		http.Error(w, "Failed to process content", http.StatusInternalServerError)
		return
	}

	// Create response
	resp := ContentResponse{
		Title:            req.Title,
		Content:          req.Content,
		Source:           req.Source,
		Author:           req.Author,
		URL:              req.URL,
		ContentHash:      contentHash,
		EntanglementHash: entanglementHash,
		ProcessedAt:      time.Now(),
		Processed:        true,
		Entities:         entities,
		Claims:           claims,
	}

	// Return response
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(resp)
}

// ExtractContentFromURL extracts content from a URL
func (h *Handler) ExtractContentFromURL(w http.ResponseWriter, r *http.Request) {
	var req struct {
		URL string `json:"url"`
	}

	// Parse request body
	err := json.NewDecoder(r.Body).Decode(&req)
	if err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	// Validate URL
	if req.URL == "" {
		http.Error(w, "URL is required", http.StatusBadRequest)
		return
	}

	// Extract content from URL
	title, content, source, author, err := h.ContentProcessor.ExtractFromURL(req.URL)
	if err != nil {
		log.Printf("Error extracting content from URL: %v", err)
		http.Error(w, "Failed to extract content from URL", http.StatusInternalServerError)
		return
	}

	// Create response
	resp := ContentRequest{
		Title:   title,
		Content: content,
		Source:  source,
		Author:  author,
		URL:     req.URL,
	}

	// Return response
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(resp)
}

// VerifyContent verifies the content by hash
func (h *Handler) VerifyContent(w http.ResponseWriter, r *http.Request) {
	var req VerificationRequest

	// Parse request body
	err := json.NewDecoder(r.Body).Decode(&req)
	if err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	// Validate content hash
	if req.ContentHash == "" {
		http.Error(w, "Content hash is required", http.StatusBadRequest)
		return
	}

	// Verify content
	verificationResult, err := h.ContentProcessor.VerifyContent(req.ContentHash, req.ReferenceURLs)
	if err != nil {
		log.Printf("Error verifying content: %v", err)
		http.Error(w, "Failed to verify content", http.StatusInternalServerError)
		return
	}

	// Return response
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(verificationResult)
}

// GetContent gets content by hash
func (h *Handler) GetContent(w http.ResponseWriter, r *http.Request) {
	// Extract content hash from URL
	vars := mux.Vars(r)
	contentHash := vars["hash"]

	if contentHash == "" {
		http.Error(w, "Content hash is required", http.StatusBadRequest)
		return
	}

	// Here you would retrieve the content from your database
	// For this example, we'll just return a mock response

	resp := ContentResponse{
		Title:             "Example News Article",
		Content:           "This is an example news article content that would be retrieved from the database.",
		Source:            "Example News Source",
		Author:            "John Doe",
		URL:               "https://example.com/article",
		ContentHash:       contentHash,
		EntanglementHash:  "abcdef1234567890",
		ProcessedAt:       time.Now().Add(-24 * time.Hour),
		Processed:         true,
		VerificationLevel: 3,
	}

	// Return response
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(resp)
}

// GetRecentContent gets recent content items
func (h *Handler) GetRecentContent(w http.ResponseWriter, r *http.Request) {
	// Parse query parameters
	limit := 10
	if limitParam := r.URL.Query().Get("limit"); limitParam != "" {
		fmt.Sscanf(limitParam, "%d", &limit)
		if limit <= 0 {
			limit = 10
		}
	}

	// Here you would retrieve recent content from your database
	// For this example, we'll just return a mock response

	items := make([]ContentResponse, 0, limit)
	for i := 0; i < limit; i++ {
		item := ContentResponse{
			Title:             fmt.Sprintf("Example News Article %d", i+1),
			Content:           fmt.Sprintf("This is example content for article %d that demonstrates how content is displayed.", i+1),
			Source:            "Example News Source",
			Author:            "John Doe",
			URL:               fmt.Sprintf("https://example.com/article/%d", i+1),
			ContentHash:       fmt.Sprintf("hash%d", i+1),
			EntanglementHash:  fmt.Sprintf("entanglement%d", i+1),
			ProcessedAt:       time.Now().Add(-time.Duration(i) * 24 * time.Hour),
			Processed:         true,
			VerificationLevel: i % 5, // Random verification level for demonstration
		}
		items = append(items, item)
	}

	// Return response
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(items)
}

// SearchContent searches for content by query
func (h *Handler) SearchContent(w http.ResponseWriter, r *http.Request) {
	// Parse query parameters
	query := r.URL.Query().Get("q")
	limit := 10
	if limitParam := r.URL.Query().Get("limit"); limitParam != "" {
		fmt.Sscanf(limitParam, "%d", &limit)
		if limit <= 0 {
			limit = 10
		}
	}

	if query == "" {
		http.Error(w, "Search query is required", http.StatusBadRequest)
		return
	}

	// Here you would search for content in your database
	// For this example, we'll just return a mock response with items that include the query

	items := make([]ContentResponse, 0, limit)
	for i := 0; i < limit; i++ {
		title := fmt.Sprintf("Article about %s - Item %d", query, i+1)
		content := fmt.Sprintf("This article discusses %s in detail and provides insights about related topics.", query)

		item := ContentResponse{
			Title:             title,
			Content:           content,
			Source:            "Search Results Source",
			Author:            "Jane Smith",
			URL:               fmt.Sprintf("https://example.com/search-result/%d", i+1),
			ContentHash:       fmt.Sprintf("search%d", i+1),
			EntanglementHash:  fmt.Sprintf("entgl%d", i+1),
			ProcessedAt:       time.Now().Add(-time.Duration(i) * 12 * time.Hour),
			Processed:         true,
			VerificationLevel: 2, // Default verification level for demonstration
		}
		items = append(items, item)
	}

	// Return response
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(items)
}

// CrossReferenceContent cross-references content with other sources
func (h *Handler) CrossReferenceContent(w http.ResponseWriter, r *http.Request) {
	var req VerificationRequest

	// Parse request body
	err := json.NewDecoder(r.Body).Decode(&req)
	if err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	// Validate content hash
	if req.ContentHash == "" {
		http.Error(w, "Content hash is required", http.StatusBadRequest)
		return
	}

	// Verify content with cross-references
	verificationResult, err := h.ContentProcessor.VerifyContent(req.ContentHash, req.ReferenceURLs)
	if err != nil {
		log.Printf("Error cross-referencing content: %v", err)
		http.Error(w, "Failed to cross-reference content", http.StatusInternalServerError)
		return
	}

	// Return response
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(verificationResult)
}

// GetVerification gets verification details for content
func (h *Handler) GetVerification(w http.ResponseWriter, r *http.Request) {
	// Extract content hash from URL
	vars := mux.Vars(r)
	contentHash := vars["hash"]

	if contentHash == "" {
		http.Error(w, "Content hash is required", http.StatusBadRequest)
		return
	}

	// Create a mock verification response
	verifiedClaims := []map[string]interface{}{
		{
			"claim_id": "claim1",
			"text":     "This is a verified claim from the article.",
			"score":    0.85,
			"supporting_references": []map[string]interface{}{
				{
					"url":           "https://example.com/reference1",
					"title":         "Supporting Reference 1",
					"source":        "Trusted Source A",
					"content_hash":  "ref1hash",
					"support_score": 0.9,
				},
			},
		},
		{
			"claim_id": "claim2",
			"text":     "This is another verified claim with strong supporting evidence.",
			"score":    0.92,
		},
	}

	disputedClaims := []map[string]interface{}{
		{
			"claim_id": "claim3",
			"text":     "This is a disputed claim that has contradicting evidence.",
			"score":    0.3,
			"disputed_by": []map[string]interface{}{
				{
					"url":           "https://example.com/disputing-source",
					"title":         "Contradicting Evidence",
					"source":        "Fact-Check Organization",
					"content_hash":  "disphash",
					"dispute_score": 0.75,
				},
			},
		},
	}

	references := []map[string]interface{}{
		{
			"url":           "https://example.com/reference1",
			"title":         "Supporting Reference 1",
			"source":        "Trusted Source A",
			"content_hash":  "ref1hash",
			"support_score": 0.9,
		},
		{
			"url":           "https://example.com/disputing-source",
			"title":         "Contradicting Evidence",
			"source":        "Fact-Check Organization",
			"content_hash":  "disphash",
			"dispute_score": 0.75,
		},
	}

	// Calculate verification score based on claims
	totalScore := 0.0
	for _, claim := range verifiedClaims {
		totalScore += claim["score"].(float64)
	}
	for _, claim := range disputedClaims {
		totalScore -= claim["score"].(float64)
	}

	// Normalize score between 0 and 1
	claimCount := float64(len(verifiedClaims) + len(disputedClaims))
	verificationScore := 0.5 // Default
	if claimCount > 0 {
		verificationScore = (totalScore/claimCount + 1) / 2 // Scale from [-1,1] to [0,1]
	}

	resp := VerificationResponse{
		ContentHash:       contentHash,
		VerificationScore: verificationScore,
		VerifiedClaims:    verifiedClaims,
		DisputedClaims:    disputedClaims,
		References:        references,
		Timestamp:         time.Now(),
	}

	// Return response
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(resp)
}

// GetSystemStatus gets the status of the system
func (h *Handler) GetSystemStatus(w http.ResponseWriter, r *http.Request) {
	// In a real implementation, this would query the consensus network
	// For now, we'll return mock data

	resp := SystemStatusResponse{
		ActiveNodes:             12,
		VerifiedContent:         142,
		AverageVerificationTime: 8.5, // seconds
		SystemHealth:            "Optimal",
	}

	// Return response
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(resp)
}

// GetSourceTrustScore gets the trust score for a source
func (h *Handler) GetSourceTrustScore(w http.ResponseWriter, r *http.Request) {
	// Extract source from URL
	vars := mux.Vars(r)
	source := vars["source"]

	if source == "" {
		http.Error(w, "Source is required", http.StatusBadRequest)
		return
	}

	// In a real implementation, this would query a database of source trust scores
	// For now, we'll return a mock response

	// Create a deterministic but randomized score based on the source name
	trustScoreMap := map[string]float64{
		"bbc.com":            0.92,
		"nytimes.com":        0.89,
		"reuters.com":        0.95,
		"theguardian.com":    0.87,
		"apnews.com":         0.94,
		"cnn.com":            0.78,
		"foxnews.com":        0.71,
		"washingtonpost.com": 0.86,
		"wsj.com":            0.85,
		"economist.com":      0.91,
	}

	// Default score if source is not in our predefined map
	var trustScore float64 = 0.5

	// Check if this is a known source
	lowercaseSource := strings.ToLower(source)
	for knownSource, score := range trustScoreMap {
		if strings.Contains(lowercaseSource, knownSource) {
			trustScore = score
			break
		}
	}

	// Return response
	response := struct {
		Source string  `json:"source"`
		Score  float64 `json:"score"`
	}{
		Source: source,
		Score:  trustScore,
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(response)
}

// LoginRequest represents the login request body
type LoginRequest struct {
	Username string `json:"username"`
	Password string `json:"password"`
}

// LoginResponse represents the login response
type LoginResponse struct {
	Token     string   `json:"token"`
	UserID    string   `json:"user_id"`
	Username  string   `json:"username"`
	UserRoles []string `json:"user_roles"`
}

// Login handles user authentication with post-quantum security
func (h *Handler) Login(w http.ResponseWriter, r *http.Request) {
	var req LoginRequest

	// Parse request body
	err := json.NewDecoder(r.Body).Decode(&req)
	if err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	// Validate request
	if req.Username == "" || req.Password == "" {
		http.Error(w, "Username and password are required", http.StatusBadRequest)
		return
	}

	// In a real implementation, this would validate credentials against a database
	// For now, we'll accept any login with a mock user

	// Mock user data
	userID := fmt.Sprintf("user_%s", hashString(req.Username))
	userRoles := []string{"user"}

	// Add admin role for specific users
	if req.Username == "admin" {
		userRoles = append(userRoles, "admin")
	}

	// Generate post-quantum secure token
	token, err := h.AuthService.CreatePQToken(userID, userRoles)
	if err != nil {
		log.Printf("Error creating token: %v", err)
		http.Error(w, "Authentication failed", http.StatusInternalServerError)
		return
	}

	// Create response
	resp := LoginResponse{
		Token:     token,
		UserID:    userID,
		Username:  req.Username,
		UserRoles: userRoles,
	}

	// Return response
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(resp)
}

// RegisterRequest represents the registration request body
type RegisterRequest struct {
	Username string `json:"username"`
	Password string `json:"password"`
	Email    string `json:"email"`
}

// Register handles user registration
func (h *Handler) Register(w http.ResponseWriter, r *http.Request) {
	var req RegisterRequest

	// Parse request body
	err := json.NewDecoder(r.Body).Decode(&req)
	if err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	// Validate request
	if req.Username == "" || req.Password == "" || req.Email == "" {
		http.Error(w, "Username, password, and email are required", http.StatusBadRequest)
		return
	}

	// In a real implementation, this would create a user in the database
	// For now, we'll just return a success response

	// Generate user ID
	userID := fmt.Sprintf("user_%s", hashString(req.Username))

	// Create response
	resp := struct {
		UserID   string `json:"user_id"`
		Username string `json:"username"`
		Message  string `json:"message"`
	}{
		UserID:   userID,
		Username: req.Username,
		Message:  "Registration successful",
	}

	// Return response
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(resp)
}

// Helper function to generate a simple hash of a string
func hashString(s string) string {
	h := sha256.New()
	h.Write([]byte(s))
	return fmt.Sprintf("%x", h.Sum(nil))[:8]
}

// ServeHTTP allows Handler to satisfy http.Handler
func (h *Handler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	// Create a new router for each request
	router := mux.NewRouter()

	// Set up routes
	h.SetupRoutes(router)

	// Serve the request
	router.ServeHTTP(w, r)
}
