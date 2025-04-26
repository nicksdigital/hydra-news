package api

import (
	"sync"
	"time"
)

// RateLimiter implements a token bucket rate limiter
type RateLimiter struct {
	requestLimit int
	window       time.Duration
	clients      map[string]*ClientBucket
	mutex        sync.RWMutex
	cleanupTicker *time.Ticker
}

// ClientBucket tracks request counts for a client
type ClientBucket struct {
	tokens        int
	lastRefill    time.Time
	lastRequested time.Time
}

// NewRateLimiter creates a new rate limiter
func NewRateLimiter(requestLimit int, window time.Duration) *RateLimiter {
	limiter := &RateLimiter{
		requestLimit: requestLimit,
		window:       window,
		clients:      make(map[string]*ClientBucket),
		cleanupTicker: time.NewTicker(10 * time.Minute),
	}
	
	// Start cleanup goroutine to prevent memory leaks
	go limiter.cleanup()
	
	return limiter
}

// Allow checks if a request is allowed based on rate limits
func (rl *RateLimiter) Allow(clientID string) bool {
	rl.mutex.Lock()
	defer rl.mutex.Unlock()
	
	now := time.Now()
	
	// Get or create client bucket
	bucket, exists := rl.clients[clientID]
	if !exists {
		bucket = &ClientBucket{
			tokens:        rl.requestLimit,
			lastRefill:    now,
			lastRequested: now,
		}
		rl.clients[clientID] = bucket
	}
	
	// Calculate time since last refill
	elapsed := now.Sub(bucket.lastRefill)
	
	// Refill tokens based on elapsed time
	if elapsed >= rl.window {
		bucket.tokens = rl.requestLimit
		bucket.lastRefill = now
	} else {
		// Partial refill based on elapsed time
		tokensToAdd := int(float64(elapsed) / float64(rl.window) * float64(rl.requestLimit))
		if tokensToAdd > 0 {
			bucket.tokens = min(rl.requestLimit, bucket.tokens+tokensToAdd)
			bucket.lastRefill = now
		}
	}
	
	// Check if request can be allowed
	if bucket.tokens > 0 {
		bucket.tokens--
		bucket.lastRequested = now
		return true
	}
	
	return false
}

// cleanup removes old client entries to prevent memory leaks
func (rl *RateLimiter) cleanup() {
	for range rl.cleanupTicker.C {
		rl.mutex.Lock()
		
		now := time.Now()
		expiration := 3 * rl.window // Keep entries for 3x the window time
		
		for clientID, bucket := range rl.clients {
			if now.Sub(bucket.lastRequested) > expiration {
				delete(rl.clients, clientID)
			}
		}
		
		rl.mutex.Unlock()
	}
}

// min returns the minimum of two integers
func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}

// Stop the rate limiter's background tasks
func (rl *RateLimiter) Stop() {
	rl.cleanupTicker.Stop()
}
