package database

import (
	"database/sql"
	"errors"
	"fmt"
	"log"
	"time"
)

// CreateNewsContent creates a new news content entry
func (c *DBClient) CreateNewsContent(content *NewsContent) error {
	c.mutex.Lock()
	defer c.mutex.Unlock()
	
	if !c.initialized {
		return errors.New("database not initialized")
	}
	
	query := `
	INSERT INTO news_content (
		content_hash, title, content, source, author, publish_date, url, 
		entanglement_hash, created_at, updated_at, submission_ip, submitter_id, is_verified
	) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
	`
	
	_, err := c.db.Exec(
		query,
		content.ContentHash,
		content.Title,
		content.Content,
		content.Source,
		content.Author,
		content.PublishDate,
		content.URL,
		content.EntanglementHash,
		content.CreatedAt,
		content.UpdatedAt,
		content.SubmissionIP,
		content.SubmitterID,
		content.IsVerified,
	)
	
	if err != nil {
		return fmt.Errorf("failed to create news content: %w", err)
	}
	
	// Insert entities if provided
	if len(content.Entities) > 0 {
		for _, entity := range content.Entities {
			err := c.CreateEntity(entity)
			if err != nil {
				log.Printf("Warning: Failed to create entity: %v", err)
			}
		}
	}
	
	// Insert claims if provided
	if len(content.Claims) > 0 {
		for _, claim := range content.Claims {
			err := c.CreateClaim(claim)
			if err != nil {
				log.Printf("Warning: Failed to create claim: %v", err)
			}
		}
	}
	
	return nil
}

// GetNewsContent retrieves news content by hash
func (c *DBClient) GetNewsContent(contentHash string) (*NewsContent, error) {
	c.mutex.RLock()
	defer c.mutex.RUnlock()
	
	if !c.initialized {
		return nil, errors.New("database not initialized")
	}
	
	query := `
	SELECT 
		content_hash, title, content, source, author, publish_date, url, 
		entanglement_hash, created_at, updated_at, submission_ip, submitter_id, is_verified
	FROM news_content
	WHERE content_hash = ?
	`
	
	var content NewsContent
	var publishDate sql.NullTime
	var author, url, submissionIP, submitterID sql.NullString
	
	err := c.db.QueryRow(query, contentHash).Scan(
		&content.ContentHash,
		&content.Title,
		&content.Content,
		&content.Source,
		&author,
		&publishDate,
		&url,
		&content.EntanglementHash,
		&content.CreatedAt,
		&content.UpdatedAt,
		&submissionIP,
		&submitterID,
		&content.IsVerified,
	)
	
	if err != nil {
		if err == sql.ErrNoRows {
			return nil, fmt.Errorf("news content not found: %s", contentHash)
		}
		return nil, fmt.Errorf("failed to get news content: %w", err)
	}
	
	// Set nullable fields
	if author.Valid {
		content.Author = author.String
	}
	
	if publishDate.Valid {
		content.PublishDate = publishDate.Time
	}
	
	if url.Valid {
		content.URL = url.String
	}
	
	if submissionIP.Valid {
		content.SubmissionIP = submissionIP.String
	}
	
	if submitterID.Valid {
		content.SubmitterID = submitterID.String
	}
	
	// Get entities for this content
	entities, err := c.GetEntitiesByContentHash(contentHash)
	if err == nil {
		content.Entities = entities
	}
	
	// Get claims for this content
	claims, err := c.GetClaimsByContentHash(contentHash)
	if err == nil {
		content.Claims = claims
	}
	
	// Get verification for this content
	verification, err := c.GetVerification(contentHash)
	if err == nil {
		content.Verification = verification
	}
	
	return &content, nil
}

// GetRecentNewsContent retrieves recent news content
func (c *DBClient) GetRecentNewsContent(limit int) ([]*NewsContent, error) {
	c.mutex.RLock()
	defer c.mutex.RUnlock()
	
	if !c.initialized {
		return nil, errors.New("database not initialized")
	}
	
	query := `
	SELECT 
		content_hash, title, content, source, author, publish_date, url, 
		entanglement_hash, created_at, updated_at, submission_ip, submitter_id, is_verified
	FROM news_content
	ORDER BY created_at DESC
	LIMIT ?
	`
	
	rows, err := c.db.Query(query, limit)
	if err != nil {
		return nil, fmt.Errorf("failed to get recent news content: %w", err)
	}
	defer rows.Close()
	
	var contents []*NewsContent
	
	for rows.Next() {
		var content NewsContent
		var publishDate sql.NullTime
		var author, url, submissionIP, submitterID sql.NullString
		
		err := rows.Scan(
			&content.ContentHash,
			&content.Title,
			&content.Content,
			&content.Source,
			&author,
			&publishDate,
			&url,
			&content.EntanglementHash,
			&content.CreatedAt,
			&content.UpdatedAt,
			&submissionIP,
			&submitterID,
			&content.IsVerified,
		)
		
		if err != nil {
			return nil, fmt.Errorf("failed to scan news content: %w", err)
		}
		
		// Set nullable fields
		if author.Valid {
			content.Author = author.String
		}
		
		if publishDate.Valid {
			content.PublishDate = publishDate.Time
		}
		
		if url.Valid {
			content.URL = url.String
		}
		
		if submissionIP.Valid {
			content.SubmissionIP = submissionIP.String
		}
		
		if submitterID.Valid {
			content.SubmitterID = submitterID.String
		}
		
		contents = append(contents, &content)
	}
	
	// Check for errors from iterating over rows
	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("error iterating over rows: %w", err)
	}
	
	// Get entities and claims for each content
	for _, content := range contents {
		entities, err := c.GetEntitiesByContentHash(content.ContentHash)
		if err == nil {
			content.Entities = entities
		}
		
		claims, err := c.GetClaimsByContentHash(content.ContentHash)
		if err == nil {
			content.Claims = claims
		}
	}
	
	return contents, nil
}

// SearchNewsContent searches for news content
func (c *DBClient) SearchNewsContent(query string, limit int) ([]*NewsContent, error) {
	c.mutex.RLock()
	defer c.mutex.RUnlock()
	
	if !c.initialized {
		return nil, errors.New("database not initialized")
	}
	
	sqlQuery := `
	SELECT 
		content_hash, title, content, source, author, publish_date, url, 
		entanglement_hash, created_at, updated_at, submission_ip, submitter_id, is_verified
	FROM news_content
	WHERE 
		title LIKE ? OR 
		content LIKE ? OR 
		source LIKE ? OR 
		author LIKE ?
	ORDER BY created_at DESC
	LIMIT ?
	`
	
	searchParam := "%" + query + "%"
	
	rows, err := c.db.Query(sqlQuery, searchParam, searchParam, searchParam, searchParam, limit)
	if err != nil {
		return nil, fmt.Errorf("failed to search news content: %w", err)
	}
	defer rows.Close()
	
	var contents []*NewsContent
	
	for rows.Next() {
		var content NewsContent
		var publishDate sql.NullTime
		var author, url, submissionIP, submitterID sql.NullString
		
		err := rows.Scan(
			&content.ContentHash,
			&content.Title,
			&content.Content,
			&content.Source,
			&author,
			&publishDate,
			&url,
			&content.EntanglementHash,
			&content.CreatedAt,
			&content.UpdatedAt,
			&submissionIP,
			&submitterID,
			&content.IsVerified,
		)
		
		if err != nil {
			return nil, fmt.Errorf("failed to scan news content: %w", err)
		}
		
		// Set nullable fields
		if author.Valid {
			content.Author = author.String
		}
		
		if publishDate.Valid {
			content.PublishDate = publishDate.Time
		}
		
		if url.Valid {
			content.URL = url.String
		}
		
		if submissionIP.Valid {
			content.SubmissionIP = submissionIP.String
		}
		
		if submitterID.Valid {
			content.SubmitterID = submitterID.String
		}
		
		contents = append(contents, &content)
	}
	
	// Check for errors from iterating over rows
	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("error iterating over rows: %w", err)
	}
	
	return contents, nil
}
