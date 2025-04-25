package database

import (
	"database/sql"
	"errors"
	"fmt"
	"time"
)

// CreateVerification creates a new verification record
func (c *DBClient) CreateVerification(verification *Verification) error {
	c.mutex.Lock()
	defer c.mutex.Unlock()
	
	if !c.initialized {
		return errors.New("database not initialized")
	}
	
	// Start a transaction
	tx, err := c.db.Begin()
	if err != nil {
		return fmt.Errorf("failed to begin transaction: %w", err)
	}
	
	// Defer rollback in case of error
	defer func() {
		if err != nil {
			tx.Rollback()
		}
	}()
	
	// Insert verification
	query := `
	INSERT INTO verification (
		verification_id, content_hash, verification_score, verification_time, 
		verifier_node_id, consensus_round_id, verification_status
	) VALUES (?, ?, ?, ?, ?, ?, ?)
	`
	
	_, err = tx.Exec(
		query,
		verification.VerificationID,
		verification.ContentHash,
		verification.VerificationScore,
		verification.VerificationTime,
		verification.VerifierNodeID,
		verification.ConsensusRoundID,
		verification.VerificationStatus,
	)
	
	if err != nil {
		return fmt.Errorf("failed to create verification: %w", err)
	}
	
	// Insert references if provided
	if len(verification.References) > 0 {
		for _, reference := range verification.References {
			reference.VerificationID = verification.VerificationID
			err := c.createReference(tx, reference)
			if err != nil {
				return fmt.Errorf("failed to create reference: %w", err)
			}
		}
	}
	
	// Update news content as verified
	updateQuery := `
	UPDATE news_content SET is_verified = true WHERE content_hash = ?
	`
	
	_, err = tx.Exec(updateQuery, verification.ContentHash)
	if err != nil {
		return fmt.Errorf("failed to update news content: %w", err)
	}
	
	// Commit transaction
	err = tx.Commit()
	if err != nil {
		return fmt.Errorf("failed to commit transaction: %w", err)
	}
	
	return nil
}

// GetVerification retrieves verification by content hash
func (c *DBClient) GetVerification(contentHash string) (*Verification, error) {
	c.mutex.RLock()
	defer c.mutex.RUnlock()
	
	if !c.initialized {
		return nil, errors.New("database not initialized")
	}
	
	query := `
	SELECT 
		verification_id, content_hash, verification_score, verification_time, 
		verifier_node_id, consensus_round_id, verification_status
	FROM verification
	WHERE content_hash = ?
	ORDER BY verification_time DESC
	LIMIT 1
	`
	
	var verification Verification
	var consensusRoundID sql.NullString
	
	err := c.db.QueryRow(query, contentHash).Scan(
		&verification.VerificationID,
		&verification.ContentHash,
		&verification.VerificationScore,
		&verification.VerificationTime,
		&verification.VerifierNodeID,
		&consensusRoundID,
		&verification.VerificationStatus,
	)
	
	if err != nil {
		if err == sql.ErrNoRows {
			return nil, fmt.Errorf("verification not found for content hash: %s", contentHash)
		}
		return nil, fmt.Errorf("failed to get verification: %w", err)
	}
	
	// Set nullable fields
	if consensusRoundID.Valid {
		verification.ConsensusRoundID = consensusRoundID.String
	}
	
	// Get references for this verification
	references, err := c.GetReferencesByVerificationID(verification.VerificationID)
	if err == nil {
		verification.References = references
	}
	
	return &verification, nil
}

// createReference creates a new reference record (within a transaction)
func (c *DBClient) createReference(tx *sql.Tx, reference *Reference) error {
	query := `
	INSERT INTO references (
		reference_id, verification_id, content_hash, reference_url, reference_title, 
		reference_source, reference_hash, support_score, dispute_score, created_at
	) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
	`
	
	var supportScore, disputeScore sql.NullFloat64
	
	if reference.SupportScore > 0 {
		supportScore.Valid = true
		supportScore.Float64 = reference.SupportScore
	}
	
	if reference.DisputeScore > 0 {
		disputeScore.Valid = true
		disputeScore.Float64 = reference.DisputeScore
	}
	
	_, err := tx.Exec(
		query,
		reference.ReferenceID,
		reference.VerificationID,
		reference.ContentHash,
		reference.ReferenceURL,
		reference.ReferenceTitle,
		reference.ReferenceSource,
		reference.ReferenceHash,
		supportScore,
		disputeScore,
		reference.CreatedAt,
	)
	
	if err != nil {
		return fmt.Errorf("failed to create reference: %w", err)
	}
	
	return nil
}

// GetReferencesByVerificationID retrieves references for a verification ID
func (c *DBClient) GetReferencesByVerificationID(verificationID string) ([]*Reference, error) {
	c.mutex.RLock()
	defer c.mutex.RUnlock()
	
	if !c.initialized {
		return nil, errors.New("database not initialized")
	}
	
	query := `
	SELECT 
		reference_id, verification_id, content_hash, reference_url, reference_title, 
		reference_source, reference_hash, support_score, dispute_score, created_at
	FROM references
	WHERE verification_id = ?
	`
	
	rows, err := c.db.Query(query, verificationID)
	if err != nil {
		return nil, fmt.Errorf("failed to get references: %w", err)
	}
	defer rows.Close()
	
	var references []*Reference
	
	for rows.Next() {
		var reference Reference
		var referenceTitle, referenceSource, referenceHash sql.NullString
		var supportScore, disputeScore sql.NullFloat64
		
		err := rows.Scan(
			&reference.ReferenceID,
			&reference.VerificationID,
			&reference.ContentHash,
			&reference.ReferenceURL,
			&referenceTitle,
			&referenceSource,
			&referenceHash,
			&supportScore,
			&disputeScore,
			&reference.CreatedAt,
		)
		
		if err != nil {
			return nil, fmt.Errorf("failed to scan reference: %w", err)
		}
		
		// Set nullable fields
		if referenceTitle.Valid {
			reference.ReferenceTitle = referenceTitle.String
		}
		
		if referenceSource.Valid {
			reference.ReferenceSource = referenceSource.String
		}
		
		if referenceHash.Valid {
			reference.ReferenceHash = referenceHash.String
		}
		
		if supportScore.Valid {
			reference.SupportScore = supportScore.Float64
		}
		
		if disputeScore.Valid {
			reference.DisputeScore = disputeScore.Float64
		}
		
		references = append(references, &reference)
	}
	
	// Check for errors from iterating over rows
	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("error iterating over rows: %w", err)
	}
	
	return references, nil
}

// GetVerificationsByNodeID retrieves verifications done by a specific node
func (c *DBClient) GetVerificationsByNodeID(nodeID string, limit int) ([]*Verification, error) {
	c.mutex.RLock()
	defer c.mutex.RUnlock()
	
	if !c.initialized {
		return nil, errors.New("database not initialized")
	}
	
	query := `
	SELECT 
		verification_id, content_hash, verification_score, verification_time, 
		verifier_node_id, consensus_round_id, verification_status
	FROM verification
	WHERE verifier_node_id = ?
	ORDER BY verification_time DESC
	LIMIT ?
	`
	
	rows, err := c.db.Query(query, nodeID, limit)
	if err != nil {
		return nil, fmt.Errorf("failed to get verifications: %w", err)
	}
	defer rows.Close()
	
	var verifications []*Verification
	
	for rows.Next() {
		var verification Verification
		var consensusRoundID sql.NullString
		
		err := rows.Scan(
			&verification.VerificationID,
			&verification.ContentHash,
			&verification.VerificationScore,
			&verification.VerificationTime,
			&verification.VerifierNodeID,
			&consensusRoundID,
			&verification.VerificationStatus,
		)
		
		if err != nil {
			return nil, fmt.Errorf("failed to scan verification: %w", err)
		}
		
		// Set nullable fields
		if consensusRoundID.Valid {
			verification.ConsensusRoundID = consensusRoundID.String
		}
		
		verifications = append(verifications, &verification)
	}
	
	// Check for errors from iterating over rows
	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("error iterating over rows: %w", err)
	}
	
	// Get references for each verification
	for _, verification := range verifications {
		references, err := c.GetReferencesByVerificationID(verification.VerificationID)
		if err == nil {
			verification.References = references
		}
	}
	
	return verifications, nil
}

// UpdateVerificationStatus updates the status of a verification
func (c *DBClient) UpdateVerificationStatus(verificationID, status string) error {
	c.mutex.Lock()
	defer c.mutex.Unlock()
	
	if !c.initialized {
		return errors.New("database not initialized")
	}
	
	query := `
	UPDATE verification 
	SET verification_status = ? 
	WHERE verification_id = ?
	`
	
	_, err := c.db.Exec(query, status, verificationID)
	if err != nil {
		return fmt.Errorf("failed to update verification status: %w", err)
	}
	
	return nil
}

// GetRecentVerifications retrieves recent verifications
func (c *DBClient) GetRecentVerifications(limit int) ([]*Verification, error) {
	c.mutex.RLock()
	defer c.mutex.RUnlock()
	
	if !c.initialized {
		return nil, errors.New("database not initialized")
	}
	
	query := `
	SELECT 
		verification_id, content_hash, verification_score, verification_time, 
		verifier_node_id, consensus_round_id, verification_status
	FROM verification
	ORDER BY verification_time DESC
	LIMIT ?
	`
	
	rows, err := c.db.Query(query, limit)
	if err != nil {
		return nil, fmt.Errorf("failed to get recent verifications: %w", err)
	}
	defer rows.Close()
	
	var verifications []*Verification
	
	for rows.Next() {
		var verification Verification
		var consensusRoundID sql.NullString
		
		err := rows.Scan(
			&verification.VerificationID,
			&verification.ContentHash,
			&verification.VerificationScore,
			&verification.VerificationTime,
			&verification.VerifierNodeID,
			&consensusRoundID,
			&verification.VerificationStatus,
		)
		
		if err != nil {
			return nil, fmt.Errorf("failed to scan verification: %w", err)
		}
		
		// Set nullable fields
		if consensusRoundID.Valid {
			verification.ConsensusRoundID = consensusRoundID.String
		}
		
		verifications = append(verifications, &verification)
	}
	
	// Check for errors from iterating over rows
	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("error iterating over rows: %w", err)
	}
	
	return verifications, nil
}
