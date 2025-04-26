package consensus

import (
	"fmt"
	"sync"
	"time"
)

// ReputationConfig contains configuration for the reputation system
type ReputationConfig struct {
	InitialScore       float64       // Initial score for new peers (0.0-1.0)
	BootstrapNodeBonus float64       // Bonus for bootstrap nodes
	MinScore           float64       // Minimum score a peer can have
	MaxScore           float64       // Maximum score a peer can have
	ScoreDecayInterval time.Duration // Interval for score decay
	ScoreDecayFactor   float64       // Factor to multiply score by during decay
	SuccessIncrement   float64       // Amount to increase score on success
	FailurePenalty     float64       // Amount to decrease score on failure
	MaliciousPenalty   float64       // Amount to decrease score on malicious behavior
	EjectionThreshold  float64       // Score below which nodes are ejected
	ProbationPeriod    time.Duration // Period before trusted status
	ProbationThreshold float64       // Score required to pass probation
	ScoreHistoryLength int           // Number of score events to keep in history
}

// DefaultReputationConfig creates a default reputation configuration
func DefaultReputationConfig() ReputationConfig {
	return ReputationConfig{
		InitialScore:       0.5,
		BootstrapNodeBonus: 0.2,
		MinScore:           0.0,
		MaxScore:           1.0,
		ScoreDecayInterval: 24 * time.Hour,
		ScoreDecayFactor:   0.95,
		SuccessIncrement:   0.01,
		FailurePenalty:     0.05,
		MaliciousPenalty:   0.2,
		EjectionThreshold:  0.2,
		ProbationPeriod:    48 * time.Hour,
		ProbationThreshold: 0.7,
		ScoreHistoryLength: 100,
	}
}

// ScoreEvent represents a single reputation score change event
type ScoreEvent struct {
	Timestamp time.Time
	OldScore  float64
	NewScore  float64
	Reason    string
}

// ReputationData contains all reputation data for a peer
type ReputationData struct {
	PeerID            string
	Score             float64
	FirstSeen         time.Time
	LastScoreUpdate   time.Time
	ConsensusSuccess  int
	ConsensusFailure  int
	MaliciousActions  int
	TrustedSince      *time.Time
	Events            []ScoreEvent
	TotalInteractions int
}

// ReputationManager manages peer reputation scores
type ReputationManager struct {
	config      ReputationConfig
	reputations map[string]*ReputationData
	repMutex    sync.RWMutex
	decayTicker *time.Ticker
	quit        chan struct{}
}

// NewReputationManager creates a new reputation manager
func NewReputationManager(config ReputationConfig) *ReputationManager {
	return &ReputationManager{
		config:      config,
		reputations: make(map[string]*ReputationData),
		quit:        make(chan struct{}),
	}
}

// Start begins the reputation management system
func (rm *ReputationManager) Start() {
	rm.decayTicker = time.NewTicker(rm.config.ScoreDecayInterval)

	go func() {
		for {
			select {
			case <-rm.quit:
				return
			case <-rm.decayTicker.C:
				rm.decayScores()
			}
		}
	}()
}

// Stop stops the reputation management system
func (rm *ReputationManager) Stop() {
	close(rm.quit)
	if rm.decayTicker != nil {
		rm.decayTicker.Stop()
	}
}

// RegisterPeer registers a new peer with the reputation system
func (rm *ReputationManager) RegisterPeer(peerID string, isBootstrapNode bool) {
	rm.repMutex.Lock()
	defer rm.repMutex.Unlock()

	// Check if peer already exists
	if _, exists := rm.reputations[peerID]; exists {
		return
	}

	// Initialize score - bootstrap nodes get a bonus
	initialScore := rm.config.InitialScore
	if isBootstrapNode {
		initialScore += rm.config.BootstrapNodeBonus
		if initialScore > rm.config.MaxScore {
			initialScore = rm.config.MaxScore
		}
	}

	now := time.Now()

	// Create reputation data
	repData := &ReputationData{
		PeerID:            peerID,
		Score:             initialScore,
		FirstSeen:         now,
		LastScoreUpdate:   now,
		ConsensusSuccess:  0,
		ConsensusFailure:  0,
		MaliciousActions:  0,
		TrustedSince:      nil, // Not trusted initially
		Events:            make([]ScoreEvent, 0, rm.config.ScoreHistoryLength),
		TotalInteractions: 0,
	}

	// Add initial score event
	reason := "Initial registration"
	if isBootstrapNode {
		reason += " (bootstrap node)"
	}
	repData.Events = append(repData.Events, ScoreEvent{
		Timestamp: now,
		OldScore:  0,
		NewScore:  initialScore,
		Reason:    reason,
	})

	rm.reputations[peerID] = repData
}

// RecordSuccess records a successful interaction with a peer
func (rm *ReputationManager) RecordSuccess(peerID string, reason string) {
	rm.repMutex.Lock()
	defer rm.repMutex.Unlock()

	repData, exists := rm.reputations[peerID]
	if !exists {
		fmt.Printf("Warning: Trying to record success for unknown peer %s\n", peerID)
		return
	}

	oldScore := repData.Score
	newScore := oldScore + rm.config.SuccessIncrement
	if newScore > rm.config.MaxScore {
		newScore = rm.config.MaxScore
	}

	repData.Score = newScore
	repData.ConsensusSuccess++
	repData.TotalInteractions++
	repData.LastScoreUpdate = time.Now()

	// Add event to history
	rm.addScoreEvent(repData, oldScore, newScore,
		fmt.Sprintf("Success: %s", reason))

	// Check if peer should be promoted to trusted status
	rm.checkForTrustPromotion(repData)
}

// RecordFailure records a failed interaction with a peer
func (rm *ReputationManager) RecordFailure(peerID string, reason string) {
	rm.repMutex.Lock()
	defer rm.repMutex.Unlock()

	repData, exists := rm.reputations[peerID]
	if !exists {
		fmt.Printf("Warning: Trying to record failure for unknown peer %s\n", peerID)
		return
	}

	oldScore := repData.Score
	newScore := oldScore - rm.config.FailurePenalty
	if newScore < rm.config.MinScore {
		newScore = rm.config.MinScore
	}

	repData.Score = newScore
	repData.ConsensusFailure++
	repData.TotalInteractions++
	repData.LastScoreUpdate = time.Now()

	// Add event to history
	rm.addScoreEvent(repData, oldScore, newScore,
		fmt.Sprintf("Failure: %s", reason))

	// Check if peer fell below ejection threshold
	if newScore <= rm.config.EjectionThreshold {
		repData.TrustedSince = nil // No longer trusted
	}
}

// RecordMaliciousAction records a malicious action by a peer
func (rm *ReputationManager) RecordMaliciousAction(peerID string, reason string) {
	rm.repMutex.Lock()
	defer rm.repMutex.Unlock()

	repData, exists := rm.reputations[peerID]
	if !exists {
		fmt.Printf("Warning: Trying to record malicious action for unknown peer %s\n", peerID)
		return
	}

	oldScore := repData.Score
	newScore := oldScore - rm.config.MaliciousPenalty
	if newScore < rm.config.MinScore {
		newScore = rm.config.MinScore
	}

	repData.Score = newScore
	repData.MaliciousActions++
	repData.TotalInteractions++
	repData.LastScoreUpdate = time.Now()

	// Add event to history
	rm.addScoreEvent(repData, oldScore, newScore,
		fmt.Sprintf("Malicious: %s", reason))

	// Peer is no longer trusted
	repData.TrustedSince = nil
}

// GetReputationScore gets a peer's current reputation score
func (rm *ReputationManager) GetReputationScore(peerID string) (float64, error) {
	rm.repMutex.RLock()
	defer rm.repMutex.RUnlock()

	repData, exists := rm.reputations[peerID]
	if !exists {
		return 0, fmt.Errorf("peer %s not found", peerID)
	}

	return repData.Score, nil
}

// GetReputationData gets all reputation data for a peer
func (rm *ReputationManager) GetReputationData(peerID string) (*ReputationData, error) {
	rm.repMutex.RLock()
	defer rm.repMutex.RUnlock()

	repData, exists := rm.reputations[peerID]
	if !exists {
		return nil, fmt.Errorf("peer %s not found", peerID)
	}

	// Return a copy to prevent race conditions
	dataCopy := *repData
	dataCopy.Events = make([]ScoreEvent, len(repData.Events))
	copy(dataCopy.Events, repData.Events)

	if repData.TrustedSince != nil {
		trustedSince := *repData.TrustedSince
		dataCopy.TrustedSince = &trustedSince
	}

	return &dataCopy, nil
}

// IsTrustedPeer checks if a peer is trusted
func (rm *ReputationManager) IsTrustedPeer(peerID string) (bool, error) {
	rm.repMutex.RLock()
	defer rm.repMutex.RUnlock()

	repData, exists := rm.reputations[peerID]
	if !exists {
		return false, fmt.Errorf("peer %s not found", peerID)
	}

	return repData.TrustedSince != nil, nil
}

// GetAllPeersWithMinScore gets all peers with at least the specified minimum score
func (rm *ReputationManager) GetAllPeersWithMinScore(minScore float64) []string {
	rm.repMutex.RLock()
	defer rm.repMutex.RUnlock()

	peers := []string{}
	for peerID, repData := range rm.reputations {
		if repData.Score >= minScore {
			peers = append(peers, peerID)
		}
	}

	return peers
}

// GetTrustedPeers gets all trusted peers
func (rm *ReputationManager) GetTrustedPeers() []string {
	rm.repMutex.RLock()
	defer rm.repMutex.RUnlock()

	trustedPeers := []string{}
	for peerID, repData := range rm.reputations {
		if repData.TrustedSince != nil {
			trustedPeers = append(trustedPeers, peerID)
		}
	}

	return trustedPeers
}

// RemovePeer removes a peer from the reputation system
func (rm *ReputationManager) RemovePeer(peerID string) {
	rm.repMutex.Lock()
	defer rm.repMutex.Unlock()

	delete(rm.reputations, peerID)
}

// addScoreEvent adds a score change event to a peer's history
func (rm *ReputationManager) addScoreEvent(repData *ReputationData, oldScore, newScore float64, reason string) {
	// Create the event
	event := ScoreEvent{
		Timestamp: time.Now(),
		OldScore:  oldScore,
		NewScore:  newScore,
		Reason:    reason,
	}

	// Add to history, maintaining the maximum history length
	repData.Events = append(repData.Events, event)
	if len(repData.Events) > rm.config.ScoreHistoryLength {
		// Remove oldest event(s)
		excess := len(repData.Events) - rm.config.ScoreHistoryLength
		repData.Events = repData.Events[excess:]
	}
}

// checkForTrustPromotion checks if a peer should be promoted to trusted status
func (rm *ReputationManager) checkForTrustPromotion(repData *ReputationData) {
	// If already trusted, nothing to do
	if repData.TrustedSince != nil {
		return
	}

	// Check if score is above the probation threshold
	if repData.Score < rm.config.ProbationThreshold {
		return
	}

	// Check if peer has been known for long enough
	probationEndTime := repData.FirstSeen.Add(rm.config.ProbationPeriod)
	if time.Now().Before(probationEndTime) {
		return
	}

	// Check if peer has enough interactions
	minInteractions := 10 // Minimum number of interactions to establish trust
	if repData.TotalInteractions < minInteractions {
		return
	}

	// Promote to trusted status
	now := time.Now()
	repData.TrustedSince = &now

	// Add event to history
	rm.addScoreEvent(repData, repData.Score, repData.Score,
		"Promoted to trusted status")
}

// decayScores applies score decay to all peers
func (rm *ReputationManager) decayScores() {
	rm.repMutex.Lock()
	defer rm.repMutex.Unlock()

	now := time.Now()

	for _, repData := range rm.reputations {
		// Calculate time since last update
		timeSinceUpdate := now.Sub(repData.LastScoreUpdate)

		// Skip if updated recently
		if timeSinceUpdate < rm.config.ScoreDecayInterval {
			continue
		}

		// Apply decay
		oldScore := repData.Score
		newScore := oldScore * rm.config.ScoreDecayFactor

		// Ensure score doesn't go below minimum
		if newScore < rm.config.MinScore {
			newScore = rm.config.MinScore
		}

		// Update score
		repData.Score = newScore
		repData.LastScoreUpdate = now

		// Add event to history
		rm.addScoreEvent(repData, oldScore, newScore, "Score decay")

		// Check if peer fell below ejection threshold
		if newScore <= rm.config.EjectionThreshold {
			repData.TrustedSince = nil // No longer trusted
		}
	}
}

// GetReputationStats gets overall statistics for the reputation system
func (rm *ReputationManager) GetReputationStats() map[string]interface{} {
	rm.repMutex.RLock()
	defer rm.repMutex.RUnlock()

	stats := map[string]interface{}{
		"total_peers":     len(rm.reputations),
		"trusted_peers":   0,
		"ejectable_peers": 0,
		"avg_score":       0.0,
		"min_score":       1.0,
		"max_score":       0.0,
	}

	if len(rm.reputations) == 0 {
		stats["min_score"] = 0.0
		return stats
	}

	// Calculate statistics
	totalScore := 0.0
	trustedCount := 0
	ejectableCount := 0
	minScore := 1.0
	maxScore := 0.0

	for _, repData := range rm.reputations {
		totalScore += repData.Score

		if repData.TrustedSince != nil {
			trustedCount++
		}

		if repData.Score <= rm.config.EjectionThreshold {
			ejectableCount++
		}

		if repData.Score < minScore {
			minScore = repData.Score
		}

		if repData.Score > maxScore {
			maxScore = repData.Score
		}
	}

	stats["trusted_peers"] = trustedCount
	stats["ejectable_peers"] = ejectableCount
	stats["avg_score"] = totalScore / float64(len(rm.reputations))
	stats["min_score"] = minScore
	stats["max_score"] = maxScore

	return stats
}
