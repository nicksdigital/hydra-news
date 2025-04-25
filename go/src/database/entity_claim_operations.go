package database

import (
	"database/sql"
	"errors"
	"fmt"
	"time"
)

// CreateEntity creates a new entity
func (c *DBClient) CreateEntity(entity *Entity) error {
	c.mutex.Lock()
	defer c.mutex.Unlock()
	
	if !c.initialized {
		return errors.New("database not initialized")
	}
	
	query := `
	INSERT INTO entities (
		entity_id, content_hash, entity_name, entity_type, confidence, context, 
		position_start, position_end, created_at
	) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
	`
	
	_, err := c.db.Exec(
		query,
		entity.EntityID,
		entity.ContentHash,
		entity.Name,
		entity.Type,
		entity.Confidence,
		entity.Context,
		entity.PositionStart,
		entity.PositionEnd,
		entity.CreatedAt,
	)
	
	if err != nil {
		return fmt.Errorf("failed to create entity: %w", err)
	}
	
	return nil
}

// GetEntitiesByContentHash retrieves entities for a content hash
func (c *DBClient) GetEntitiesByContentHash(contentHash string) ([]*Entity, error) {
	c.mutex.RLock()
	defer c.mutex.RUnlock()
	
	if !c.initialized {
		return nil, errors.New("database not initialized")
	}
	
	query := `
	SELECT 
		entity_id, content_hash, entity_name, entity_type, confidence, context, 
		position_start, position_end, created_at
	FROM entities
	WHERE content_hash = ?
	`
	
	rows, err := c.db.Query(query, contentHash)
	if err != nil {
		return nil, fmt.Errorf("failed to get entities: %w", err)
	}
	defer rows.Close()
	
	var entities []*Entity
	
	for rows.Next() {
		var entity Entity
		var context sql.NullString
		var posStart, posEnd sql.NullInt32
		
		err := rows.Scan(
			&entity.EntityID,
			&entity.ContentHash,
			&entity.Name,
			&entity.Type,
			&entity.Confidence,
			&context,
			&posStart,
			&posEnd,
			&entity.CreatedAt,
		)
		
		if err != nil {
			return nil, fmt.Errorf("failed to scan entity: %w", err)
		}
		
		// Set nullable fields
		if context.Valid {
			entity.Context = context.String
		}
		
		if posStart.Valid {
			entity.PositionStart = int(posStart.Int32)
		}
		
		if posEnd.Valid {
			entity.PositionEnd = int(posEnd.Int32)
		}
		
		entities = append(entities, &entity)
	}
	
	// Check for errors from iterating over rows
	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("error iterating over rows: %w", err)
	}
	
	return entities, nil
}

// CreateClaim creates a new claim
func (c *DBClient) CreateClaim(claim *Claim) error {
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
	
	// Insert claim
	query := `
	INSERT INTO claims (
		claim_id, content_hash, claim_text, source_text, confidence, claim_type, 
		position_start, position_end, created_at
	) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
	`
	
	_, err = tx.Exec(
		query,
		claim.ClaimID,
		claim.ContentHash,
		claim.ClaimText,
		claim.SourceText,
		claim.Confidence,
		claim.ClaimType,
		claim.PositionStart,
		claim.PositionEnd,
		claim.CreatedAt,
	)
	
	if err != nil {
		return fmt.Errorf("failed to create claim: %w", err)
	}
	
	// Insert claim-entity relationships if entities are provided
	if len(claim.Entities) > 0 {
		relationQuery := `
		INSERT INTO claim_entity (claim_id, entity_id, relationship)
		VALUES (?, ?, ?)
		`
		
		for _, entityID := range claim.Entities {
			_, err = tx.Exec(relationQuery, claim.ClaimID, entityID, "mentioned")
			if err != nil {
				return fmt.Errorf("failed to create claim-entity relationship: %w", err)
			}
		}
	}
	
	// Commit transaction
	err = tx.Commit()
	if err != nil {
		return fmt.Errorf("failed to commit transaction: %w", err)
	}
	
	return nil
}

// GetClaimsByContentHash retrieves claims for a content hash
func (c *DBClient) GetClaimsByContentHash(contentHash string) ([]*Claim, error) {
	c.mutex.RLock()
	defer c.mutex.RUnlock()
	
	if !c.initialized {
		return nil, errors.New("database not initialized")
	}
	
	query := `
	SELECT 
		claim_id, content_hash, claim_text, source_text, confidence, claim_type, 
		position_start, position_end, created_at
	FROM claims
	WHERE content_hash = ?
	`
	
	rows, err := c.db.Query(query, contentHash)
	if err != nil {
		return nil, fmt.Errorf("failed to get claims: %w", err)
	}
	defer rows.Close()
	
	var claims []*Claim
	
	for rows.Next() {
		var claim Claim
		var sourceText sql.NullString
		var posStart, posEnd sql.NullInt32
		
		err := rows.Scan(
			&claim.ClaimID,
			&claim.ContentHash,
			&claim.ClaimText,
			&sourceText,
			&claim.Confidence,
			&claim.ClaimType,
			&posStart,
			&posEnd,
			&claim.CreatedAt,
		)
		
		if err != nil {
			return nil, fmt.Errorf("failed to scan claim: %w", err)
		}
		
		// Set nullable fields
		if sourceText.Valid {
			claim.SourceText = sourceText.String
		}
		
		if posStart.Valid {
			claim.PositionStart = int(posStart.Int32)
		}
		
		if posEnd.Valid {
			claim.PositionEnd = int(posEnd.Int32)
		}
		
		// Get related entities
		entityQuery := `
		SELECT entity_id FROM claim_entity WHERE claim_id = ?
		`
		
		entityRows, err := c.db.Query(entityQuery, claim.ClaimID)
		if err == nil {
			defer entityRows.Close()
			
			for entityRows.Next() {
				var entityID string
				if err := entityRows.Scan(&entityID); err == nil {
					claim.Entities = append(claim.Entities, entityID)
				}
			}
		}
		
		claims = append(claims, &claim)
	}
	
	// Check for errors from iterating over rows
	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("error iterating over rows: %w", err)
	}
	
	return claims, nil
}

// GetEntityByID retrieves an entity by ID
func (c *DBClient) GetEntityByID(entityID string) (*Entity, error) {
	c.mutex.RLock()
	defer c.mutex.RUnlock()
	
	if !c.initialized {
		return nil, errors.New("database not initialized")
	}
	
	query := `
	SELECT 
		entity_id, content_hash, entity_name, entity_type, confidence, context, 
		position_start, position_end, created_at
	FROM entities
	WHERE entity_id = ?
	`
	
	var entity Entity
	var context sql.NullString
	var posStart, posEnd sql.NullInt32
	
	err := c.db.QueryRow(query, entityID).Scan(
		&entity.EntityID,
		&entity.ContentHash,
		&entity.Name,
		&entity.Type,
		&entity.Confidence,
		&context,
		&posStart,
		&posEnd,
		&entity.CreatedAt,
	)
	
	if err != nil {
		if err == sql.ErrNoRows {
			return nil, fmt.Errorf("entity not found: %s", entityID)
		}
		return nil, fmt.Errorf("failed to get entity: %w", err)
	}
	
	// Set nullable fields
	if context.Valid {
		entity.Context = context.String
	}
	
	if posStart.Valid {
		entity.PositionStart = int(posStart.Int32)
	}
	
	if posEnd.Valid {
		entity.PositionEnd = int(posEnd.Int32)
	}
	
	return &entity, nil
}

// GetClaimByID retrieves a claim by ID
func (c *DBClient) GetClaimByID(claimID string) (*Claim, error) {
	c.mutex.RLock()
	defer c.mutex.RUnlock()
	
	if !c.initialized {
		return nil, errors.New("database not initialized")
	}
	
	query := `
	SELECT 
		claim_id, content_hash, claim_text, source_text, confidence, claim_type, 
		position_start, position_end, created_at
	FROM claims
	WHERE claim_id = ?
	`
	
	var claim Claim
	var sourceText sql.NullString
	var posStart, posEnd sql.NullInt32
	
	err := c.db.QueryRow(query, claimID).Scan(
		&claim.ClaimID,
		&claim.ContentHash,
		&claim.ClaimText,
		&sourceText,
		&claim.Confidence,
		&claim.ClaimType,
		&posStart,
		&posEnd,
		&claim.CreatedAt,
	)
	
	if err != nil {
		if err == sql.ErrNoRows {
			return nil, fmt.Errorf("claim not found: %s", claimID)
		}
		return nil, fmt.Errorf("failed to get claim: %w", err)
	}
	
	// Set nullable fields
	if sourceText.Valid {
		claim.SourceText = sourceText.String
	}
	
	if posStart.Valid {
		claim.PositionStart = int(posStart.Int32)
	}
	
	if posEnd.Valid {
		claim.PositionEnd = int(posEnd.Int32)
	}
	
	// Get related entities
	entityQuery := `
	SELECT entity_id FROM claim_entity WHERE claim_id = ?
	`
	
	entityRows, err := c.db.Query(entityQuery, claim.ClaimID)
	if err == nil {
		defer entityRows.Close()
		
		for entityRows.Next() {
			var entityID string
			if err := entityRows.Scan(&entityID); err == nil {
				claim.Entities = append(claim.Entities, entityID)
			}
		}
	}
	
	return &claim, nil
}

// SearchEntities searches for entities by name or type
func (c *DBClient) SearchEntities(query string, limit int) ([]*Entity, error) {
	c.mutex.RLock()
	defer c.mutex.RUnlock()
	
	if !c.initialized {
		return nil, errors.New("database not initialized")
	}
	
	sqlQuery := `
	SELECT 
		entity_id, content_hash, entity_name, entity_type, confidence, context, 
		position_start, position_end, created_at
	FROM entities
	WHERE 
		entity_name LIKE ? OR 
		entity_type LIKE ?
	ORDER BY confidence DESC
	LIMIT ?
	`
	
	searchParam := "%" + query + "%"
	
	rows, err := c.db.Query(sqlQuery, searchParam, searchParam, limit)
	if err != nil {
		return nil, fmt.Errorf("failed to search entities: %w", err)
	}
	defer rows.Close()
	
	var entities []*Entity
	
	for rows.Next() {
		var entity Entity
		var context sql.NullString
		var posStart, posEnd sql.NullInt32
		
		err := rows.Scan(
			&entity.EntityID,
			&entity.ContentHash,
			&entity.Name,
			&entity.Type,
			&entity.Confidence,
			&context,
			&posStart,
			&posEnd,
			&entity.CreatedAt,
		)
		
		if err != nil {
			return nil, fmt.Errorf("failed to scan entity: %w", err)
		}
		
		// Set nullable fields
		if context.Valid {
			entity.Context = context.String
		}
		
		if posStart.Valid {
			entity.PositionStart = int(posStart.Int32)
		}
		
		if posEnd.Valid {
			entity.PositionEnd = int(posEnd.Int32)
		}
		
		entities = append(entities, &entity)
	}
	
	// Check for errors from iterating over rows
	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("error iterating over rows: %w", err)
	}
	
	return entities, nil
}
