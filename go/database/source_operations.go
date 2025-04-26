package database

import (
	"database/sql"
	"errors"
	"fmt"
	"time"
)

// CreateSource creates a new source
func (c *DBClient) CreateSource(source *Source) error {
	c.mutex.Lock()
	defer c.mutex.Unlock()

	if !c.initialized {
		return errors.New("database not initialized")
	}

	query := `
	INSERT INTO sources (
		source_id, source_name, domain, trust_score, verified, created_at, updated_at
	) VALUES (?, ?, ?, ?, ?, ?, ?)
	`

	var domain sql.NullString

	if source.Domain != "" {
		domain.Valid = true
		domain.String = source.Domain
	}

	_, err := c.db.Exec(
		query,
		source.SourceID,
		source.SourceName,
		domain,
		source.TrustScore,
		source.Verified,
		source.CreatedAt,
		source.UpdatedAt,
	)

	if err != nil {
		return fmt.Errorf("failed to create source: %w", err)
	}

	return nil
}

// GetSourceByID retrieves a source by ID
func (c *DBClient) GetSourceByID(sourceID string) (*Source, error) {
	c.mutex.RLock()
	defer c.mutex.RUnlock()

	if !c.initialized {
		return nil, errors.New("database not initialized")
	}

	query := `
	SELECT 
		source_id, source_name, domain, trust_score, verified, created_at, updated_at
	FROM sources
	WHERE source_id = ?
	`

	var source Source
	var domain sql.NullString

	err := c.db.QueryRow(query, sourceID).Scan(
		&source.SourceID,
		&source.SourceName,
		&domain,
		&source.TrustScore,
		&source.Verified,
		&source.CreatedAt,
		&source.UpdatedAt,
	)

	if err != nil {
		if err == sql.ErrNoRows {
			return nil, fmt.Errorf("source not found: %s", sourceID)
		}
		return nil, fmt.Errorf("failed to get source: %w", err)
	}

	// Set nullable fields
	if domain.Valid {
		source.Domain = domain.String
	}

	return &source, nil
}

// GetSourceByName retrieves a source by name
func (c *DBClient) GetSourceByName(sourceName string) (*Source, error) {
	c.mutex.RLock()
	defer c.mutex.RUnlock()

	if !c.initialized {
		return nil, errors.New("database not initialized")
	}

	query := `
	SELECT 
		source_id, source_name, domain, trust_score, verified, created_at, updated_at
	FROM sources
	WHERE source_name = ?
	`

	var source Source
	var domain sql.NullString

	err := c.db.QueryRow(query, sourceName).Scan(
		&source.SourceID,
		&source.SourceName,
		&domain,
		&source.TrustScore,
		&source.Verified,
		&source.CreatedAt,
		&source.UpdatedAt,
	)

	if err != nil {
		if err == sql.ErrNoRows {
			return nil, fmt.Errorf("source not found with name: %s", sourceName)
		}
		return nil, fmt.Errorf("failed to get source: %w", err)
	}

	// Set nullable fields
	if domain.Valid {
		source.Domain = domain.String
	}

	return &source, nil
}

// GetSourceByDomain retrieves a source by domain
func (c *DBClient) GetSourceByDomain(domainName string) (*Source, error) {
	c.mutex.RLock()
	defer c.mutex.RUnlock()

	if !c.initialized {
		return nil, errors.New("database not initialized")
	}

	query := `
	SELECT 
		source_id, source_name, domain, trust_score, verified, created_at, updated_at
	FROM sources
	WHERE domain = ?
	`

	var source Source
	var domain sql.NullString

	err := c.db.QueryRow(query, domainName).Scan(
		&source.SourceID,
		&source.SourceName,
		&domain,
		&source.TrustScore,
		&source.Verified,
		&source.CreatedAt,
		&source.UpdatedAt,
	)

	if err != nil {
		if err == sql.ErrNoRows {
			return nil, fmt.Errorf("source not found with domain: %s", domainName)
		}
		return nil, fmt.Errorf("failed to get source: %w", err)
	}

	// Set nullable fields
	if domain.Valid {
		source.Domain = domain.String
	}

	return &source, nil
}

// UpdateSourceTrustScore updates a source's trust score
func (c *DBClient) UpdateSourceTrustScore(sourceID string, trustScore float64) error {
	c.mutex.Lock()
	defer c.mutex.Unlock()

	if !c.initialized {
		return errors.New("database not initialized")
	}

	query := `
	UPDATE sources 
	SET trust_score = ?, updated_at = ? 
	WHERE source_id = ?
	`

	_, err := c.db.Exec(query, trustScore, time.Now(), sourceID)
	if err != nil {
		return fmt.Errorf("failed to update source trust score: %w", err)
	}

	return nil
}

// UpdateSourceVerificationStatus updates a source's verification status
func (c *DBClient) UpdateSourceVerificationStatus(sourceID string, verified bool) error {
	c.mutex.Lock()
	defer c.mutex.Unlock()

	if !c.initialized {
		return errors.New("database not initialized")
	}

	query := `
	UPDATE sources 
	SET verified = ?, updated_at = ? 
	WHERE source_id = ?
	`

	_, err := c.db.Exec(query, verified, time.Now(), sourceID)
	if err != nil {
		return fmt.Errorf("failed to update source verification status: %w", err)
	}

	return nil
}

// ListSources lists sources with optional filtering by verification status
func (c *DBClient) ListSources(verified *bool, limit int, offset int) ([]*Source, error) {
	c.mutex.RLock()
	defer c.mutex.RUnlock()

	if !c.initialized {
		return nil, errors.New("database not initialized")
	}

	var query string
	var args []interface{}

	if verified != nil {
		query = `
		SELECT 
			source_id, source_name, domain, trust_score, verified, created_at, updated_at
		FROM sources
		WHERE verified = ?
		ORDER BY trust_score DESC, created_at DESC
		LIMIT ? OFFSET ?
		`
		args = []interface{}{*verified, limit, offset}
	} else {
		query = `
		SELECT 
			source_id, source_name, domain, trust_score, verified, created_at, updated_at
		FROM sources
		ORDER BY trust_score DESC, created_at DESC
		LIMIT ? OFFSET ?
		`
		args = []interface{}{limit, offset}
	}

	rows, err := c.db.Query(query, args...)
	if err != nil {
		return nil, fmt.Errorf("failed to list sources: %w", err)
	}
	defer rows.Close()

	var sources []*Source

	for rows.Next() {
		var source Source
		var domain sql.NullString

		err := rows.Scan(
			&source.SourceID,
			&source.SourceName,
			&domain,
			&source.TrustScore,
			&source.Verified,
			&source.CreatedAt,
			&source.UpdatedAt,
		)

		if err != nil {
			return nil, fmt.Errorf("failed to scan source: %w", err)
		}

		// Set nullable fields
		if domain.Valid {
			source.Domain = domain.String
		}

		sources = append(sources, &source)
	}

	// Check for errors from iterating over rows
	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("error iterating over rows: %w", err)
	}

	return sources, nil
}

// SearchSources searches for sources by name or domain
func (c *DBClient) SearchSources(query string, limit int) ([]*Source, error) {
	c.mutex.RLock()
	defer c.mutex.RUnlock()

	if !c.initialized {
		return nil, errors.New("database not initialized")
	}

	sqlQuery := `
	SELECT 
		source_id, source_name, domain, trust_score, verified, created_at, updated_at
	FROM sources
	WHERE 
		source_name LIKE ? OR 
		domain LIKE ?
	ORDER BY trust_score DESC, created_at DESC
	LIMIT ?
	`

	searchParam := "%" + query + "%"

	rows, err := c.db.Query(sqlQuery, searchParam, searchParam, limit)
	if err != nil {
		return nil, fmt.Errorf("failed to search sources: %w", err)
	}
	defer rows.Close()

	var sources []*Source

	for rows.Next() {
		var source Source
		var domain sql.NullString

		err := rows.Scan(
			&source.SourceID,
			&source.SourceName,
			&domain,
			&source.TrustScore,
			&source.Verified,
			&source.CreatedAt,
			&source.UpdatedAt,
		)

		if err != nil {
			return nil, fmt.Errorf("failed to scan source: %w", err)
		}

		// Set nullable fields
		if domain.Valid {
			source.Domain = domain.String
		}

		sources = append(sources, &source)
	}

	// Check for errors from iterating over rows
	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("error iterating over rows: %w", err)
	}

	return sources, nil
}

// GetSourcesByTrustScoreRange retrieves sources within a trust score range
func (c *DBClient) GetSourcesByTrustScoreRange(minScore, maxScore float64, limit int) ([]*Source, error) {
	c.mutex.RLock()
	defer c.mutex.RUnlock()

	if !c.initialized {
		return nil, errors.New("database not initialized")
	}

	query := `
	SELECT 
		source_id, source_name, domain, trust_score, verified, created_at, updated_at
	FROM sources
	WHERE trust_score BETWEEN ? AND ?
	ORDER BY trust_score DESC, created_at DESC
	LIMIT ?
	`

	rows, err := c.db.Query(query, minScore, maxScore, limit)
	if err != nil {
		return nil, fmt.Errorf("failed to get sources by trust score range: %w", err)
	}
	defer rows.Close()

	var sources []*Source

	for rows.Next() {
		var source Source
		var domain sql.NullString

		err := rows.Scan(
			&source.SourceID,
			&source.SourceName,
			&domain,
			&source.TrustScore,
			&source.Verified,
			&source.CreatedAt,
			&source.UpdatedAt,
		)

		if err != nil {
			return nil, fmt.Errorf("failed to scan source: %w", err)
		}

		// Set nullable fields
		if domain.Valid {
			source.Domain = domain.String
		}

		sources = append(sources, &source)
	}

	// Check for errors from iterating over rows
	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("error iterating over rows: %w", err)
	}

	return sources, nil
}

// GetHighestTrustScoreSources retrieves the sources with the highest trust scores
func (c *DBClient) GetHighestTrustScoreSources(limit int) ([]*Source, error) {
	c.mutex.RLock()
	defer c.mutex.RUnlock()

	if !c.initialized {
		return nil, errors.New("database not initialized")
	}

	query := `
	SELECT 
		source_id, source_name, domain, trust_score, verified, created_at, updated_at
	FROM sources
	ORDER BY trust_score DESC
	LIMIT ?
	`

	rows, err := c.db.Query(query, limit)
	if err != nil {
		return nil, fmt.Errorf("failed to get highest trust score sources: %w", err)
	}
	defer rows.Close()

	var sources []*Source

	for rows.Next() {
		var source Source
		var domain sql.NullString

		err := rows.Scan(
			&source.SourceID,
			&source.SourceName,
			&domain,
			&source.TrustScore,
			&source.Verified,
			&source.CreatedAt,
			&source.UpdatedAt,
		)

		if err != nil {
			return nil, fmt.Errorf("failed to scan source: %w", err)
		}

		// Set nullable fields
		if domain.Valid {
			source.Domain = domain.String
		}

		sources = append(sources, &source)
	}

	// Check for errors from iterating over rows
	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("error iterating over rows: %w", err)
	}

	return sources, nil
}

// GetVerifiedSources retrieves verified sources
func (c *DBClient) GetVerifiedSources(limit int) ([]*Source, error) {
	c.mutex.RLock()
	defer c.mutex.RUnlock()

	if !c.initialized {
		return nil, errors.New("database not initialized")
	}

	query := `
	SELECT 
		source_id, source_name, domain, trust_score, verified, created_at, updated_at
	FROM sources
	WHERE verified = true
	ORDER BY trust_score DESC
	LIMIT ?
	`

	rows, err := c.db.Query(query, limit)
	if err != nil {
		return nil, fmt.Errorf("failed to get verified sources: %w", err)
	}
	defer rows.Close()

	var sources []*Source

	for rows.Next() {
		var source Source
		var domain sql.NullString

		err := rows.Scan(
			&source.SourceID,
			&source.SourceName,
			&domain,
			&source.TrustScore,
			&source.Verified,
			&source.CreatedAt,
			&source.UpdatedAt,
		)

		if err != nil {
			return nil, fmt.Errorf("failed to scan source: %w", err)
		}

		// Set nullable fields
		if domain.Valid {
			source.Domain = domain.String
		}

		sources = append(sources, &source)
	}

	// Check for errors from iterating over rows
	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("error iterating over rows: %w", err)
	}

	return sources, nil
}

// GetSourcesCount gets the total count of sources
func (c *DBClient) GetSourcesCount(onlyVerified bool) (int, error) {
	c.mutex.RLock()
	defer c.mutex.RUnlock()

	if !c.initialized {
		return 0, errors.New("database not initialized")
	}

	var query string

	if onlyVerified {
		query = "SELECT COUNT(*) FROM sources WHERE verified = true"
	} else {
		query = "SELECT COUNT(*) FROM sources"
	}

	var count int
	err := c.db.QueryRow(query).Scan(&count)
	if err != nil {
		return 0, fmt.Errorf("failed to get sources count: %w", err)
	}

	return count, nil
}

// GetSourceContentStats gets content statistics for a source
func (c *DBClient) GetSourceContentStats(sourceID string) (map[string]interface{}, error) {
	c.mutex.RLock()
	defer c.mutex.RUnlock()

	if !c.initialized {
		return nil, errors.New("database not initialized")
	}

	stats := make(map[string]interface{})

	// Get total content count
	contentQuery := "SELECT COUNT(*) FROM news_content WHERE source = ?"
	var contentCount int
	err := c.db.QueryRow(contentQuery, sourceID).Scan(&contentCount)
	if err != nil {
		return nil, fmt.Errorf("failed to get content count: %w", err)
	}
	stats["total_content"] = contentCount

	// Get verified content count
	verifiedQuery := "SELECT COUNT(*) FROM news_content WHERE source = ? AND is_verified = true"
	var verifiedCount int
	err = c.db.QueryRow(verifiedQuery, sourceID).Scan(&verifiedCount)
	if err != nil {
		return nil, fmt.Errorf("failed to get verified content count: %w", err)
	}
	stats["verified_content"] = verifiedCount

	// Get average verification score
	if verifiedCount > 0 {
		scoreQuery := `
		SELECT AVG(v.verification_score)
		FROM news_content c
		JOIN verification v ON c.content_hash = v.content_hash
		WHERE c.source = ?
		`
		var avgScore float64
		err = c.db.QueryRow(scoreQuery, sourceID).Scan(&avgScore)
		if err != nil {
			return nil, fmt.Errorf("failed to get average verification score: %w", err)
		}
		stats["average_verification_score"] = avgScore
	} else {
		stats["average_verification_score"] = 0.0
	}

	// Get content count by month (last 6 months)
	monthlyQuery := `
	SELECT strftime('%Y-%m', created_at) as month, COUNT(*) as count
	FROM news_content
	WHERE source = ? AND created_at >= date('now', '-6 months')
	GROUP BY month
	ORDER BY month DESC
	`

	monthlyRows, err := c.db.Query(monthlyQuery, sourceID)
	if err != nil {
		return nil, fmt.Errorf("failed to get monthly content counts: %w", err)
	}
	defer monthlyRows.Close()

	monthlyStats := make(map[string]int)
	for monthlyRows.Next() {
		var month string
		var count int
		err := monthlyRows.Scan(&month, &count)
		if err != nil {
			return nil, fmt.Errorf("failed to scan monthly content count: %w", err)
		}
		monthlyStats[month] = count
	}

	// Check for errors from iterating over rows
	if err := monthlyRows.Err(); err != nil {
		return nil, fmt.Errorf("error iterating over monthly rows: %w", err)
	}

	stats["monthly_counts"] = monthlyStats

	return stats, nil
}
