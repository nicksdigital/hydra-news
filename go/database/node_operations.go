package database

import (
	"database/sql"
	"errors"
	"fmt"
	"time"
)

// CreateNode creates a new node record
func (c *DBClient) CreateNode(node *Node) error {
	c.mutex.Lock()
	defer c.mutex.Unlock()
	
	if !c.initialized {
		return errors.New("database not initialized")
	}
	
	query := `
	INSERT INTO nodes (
		node_id, node_address, qzkp_address, public_key, reputation, first_seen, 
		last_seen, status, geo_region, node_version, is_bootstrap
	) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
	`
	
	var geoRegion, nodeVersion sql.NullString
	
	if node.GeoRegion != "" {
		geoRegion.Valid = true
		geoRegion.String = node.GeoRegion
	}
	
	if node.NodeVersion != "" {
		nodeVersion.Valid = true
		nodeVersion.String = node.NodeVersion
	}
	
	_, err := c.db.Exec(
		query,
		node.NodeID,
		node.NodeAddress,
		node.QZKPAddress,
		node.PublicKey,
		node.Reputation,
		node.FirstSeen,
		node.LastSeen,
		node.Status,
		geoRegion,
		nodeVersion,
		node.IsBootstrap,
	)
	
	if err != nil {
		return fmt.Errorf("failed to create node: %w", err)
	}
	
	return nil
}

// GetNodeByID retrieves a node by ID
func (c *DBClient) GetNodeByID(nodeID string) (*Node, error) {
	c.mutex.RLock()
	defer c.mutex.RUnlock()
	
	if !c.initialized {
		return nil, errors.New("database not initialized")
	}
	
	query := `
	SELECT 
		node_id, node_address, qzkp_address, public_key, reputation, first_seen, 
		last_seen, status, geo_region, node_version, is_bootstrap
	FROM nodes
	WHERE node_id = ?
	`
	
	var node Node
	var geoRegion, nodeVersion sql.NullString
	
	err := c.db.QueryRow(query, nodeID).Scan(
		&node.NodeID,
		&node.NodeAddress,
		&node.QZKPAddress,
		&node.PublicKey,
		&node.Reputation,
		&node.FirstSeen,
		&node.LastSeen,
		&node.Status,
		&geoRegion,
		&nodeVersion,
		&node.IsBootstrap,
	)
	
	if err != nil {
		if err == sql.ErrNoRows {
			return nil, fmt.Errorf("node not found: %s", nodeID)
		}
		return nil, fmt.Errorf("failed to get node: %w", err)
	}
	
	// Set nullable fields
	if geoRegion.Valid {
		node.GeoRegion = geoRegion.String
	}
	
	if nodeVersion.Valid {
		node.NodeVersion = nodeVersion.String
	}
	
	return &node, nil
}

// GetNodeByQZKPAddress retrieves a node by QZKP address
func (c *DBClient) GetNodeByQZKPAddress(qzkpAddress string) (*Node, error) {
	c.mutex.RLock()
	defer c.mutex.RUnlock()
	
	if !c.initialized {
		return nil, errors.New("database not initialized")
	}
	
	query := `
	SELECT 
		node_id, node_address, qzkp_address, public_key, reputation, first_seen, 
		last_seen, status, geo_region, node_version, is_bootstrap
	FROM nodes
	WHERE qzkp_address = ?
	`
	
	var node Node
	var geoRegion, nodeVersion sql.NullString
	
	err := c.db.QueryRow(query, qzkpAddress).Scan(
		&node.NodeID,
		&node.NodeAddress,
		&node.QZKPAddress,
		&node.PublicKey,
		&node.Reputation,
		&node.FirstSeen,
		&node.LastSeen,
		&node.Status,
		&geoRegion,
		&nodeVersion,
		&node.IsBootstrap,
	)
	
	if err != nil {
		if err == sql.ErrNoRows {
			return nil, fmt.Errorf("node not found with QZKP address: %s", qzkpAddress)
		}
		return nil, fmt.Errorf("failed to get node: %w", err)
	}
	
	// Set nullable fields
	if geoRegion.Valid {
		node.GeoRegion = geoRegion.String
	}
	
	if nodeVersion.Valid {
		node.NodeVersion = nodeVersion.String
	}
	
	return &node, nil
}

// UpdateNodeStatus updates a node's status and last seen time
func (c *DBClient) UpdateNodeStatus(nodeID, status string) error {
	c.mutex.Lock()
	defer c.mutex.Unlock()
	
	if !c.initialized {
		return errors.New("database not initialized")
	}
	
	query := `
	UPDATE nodes SET status = ?, last_seen = ? WHERE node_id = ?
	`
	
	_, err := c.db.Exec(query, status, time.Now(), nodeID)
	if err != nil {
		return fmt.Errorf("failed to update node status: %w", err)
	}
	
	return nil
}

// UpdateNodeReputation updates a node's reputation
func (c *DBClient) UpdateNodeReputation(nodeID string, reputation float64) error {
	c.mutex.Lock()
	defer c.mutex.Unlock()
	
	if !c.initialized {
		return errors.New("database not initialized")
	}
	
	query := `
	UPDATE nodes SET reputation = ? WHERE node_id = ?
	`
	
	_, err := c.db.Exec(query, reputation, nodeID)
	if err != nil {
		return fmt.Errorf("failed to update node reputation: %w", err)
	}
	
	return nil
}

// GetActiveNodes retrieves all active nodes
func (c *DBClient) GetActiveNodes() ([]*Node, error) {
	c.mutex.RLock()
	defer c.mutex.RUnlock()
	
	if !c.initialized {
		return nil, errors.New("database not initialized")
	}
	
	query := `
	SELECT 
		node_id, node_address, qzkp_address, public_key, reputation, first_seen, 
		last_seen, status, geo_region, node_version, is_bootstrap
	FROM nodes
	WHERE status = 'active'
	ORDER BY reputation DESC
	`
	
	rows, err := c.db.Query(query)
	if err != nil {
		return nil, fmt.Errorf("failed to get active nodes: %w", err)
	}
	defer rows.Close()
	
	var nodes []*Node
	
	for rows.Next() {
		var node Node
		var geoRegion, nodeVersion sql.NullString
		
		err := rows.Scan(
			&node.NodeID,
			&node.NodeAddress,
			&node.QZKPAddress,
			&node.PublicKey,
			&node.Reputation,
			&node.FirstSeen,
			&node.LastSeen,
			&node.Status,
			&geoRegion,
			&nodeVersion,
			&node.IsBootstrap,
		)
		
		if err != nil {
			return nil, fmt.Errorf("failed to scan node: %w", err)
		}
		
		// Set nullable fields
		if geoRegion.Valid {
			node.GeoRegion = geoRegion.String
		}
		
		if nodeVersion.Valid {
			node.NodeVersion = nodeVersion.String
		}
		
		nodes = append(nodes, &node)
	}
	
	// Check for errors from iterating over rows
	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("error iterating over rows: %w", err)
	}
	
	return nodes, nil
}

// GetBootstrapNodes retrieves all bootstrap nodes
func (c *DBClient) GetBootstrapNodes() ([]*Node, error) {
	c.mutex.RLock()
	defer c.mutex.RUnlock()
	
	if !c.initialized {
		return nil, errors.New("database not initialized")
	}
	
	query := `
	SELECT 
		node_id, node_address, qzkp_address, public_key, reputation, first_seen, 
		last_seen, status, geo_region, node_version, is_bootstrap
	FROM nodes
	WHERE is_bootstrap = true
	`
	
	rows, err := c.db.Query(query)
	if err != nil {
		return nil, fmt.Errorf("failed to get bootstrap nodes: %w", err)
	}
	defer rows.Close()
	
	var nodes []*Node
	
	for rows.Next() {
		var node Node
		var geoRegion, nodeVersion sql.NullString
		
		err := rows.Scan(
			&node.NodeID,
			&node.NodeAddress,
			&node.QZKPAddress,
			&node.PublicKey,
			&node.Reputation,
			&node.FirstSeen,
			&node.LastSeen,
			&node.Status,
			&geoRegion,
			&nodeVersion,
			&node.IsBootstrap,
		)
		
		if err != nil {
			return nil, fmt.Errorf("failed to scan node: %w", err)
		}
		
		// Set nullable fields
		if geoRegion.Valid {
			node.GeoRegion = geoRegion.String
		}
		
		if nodeVersion.Valid {
			node.NodeVersion = nodeVersion.String
		}
		
		nodes = append(nodes, &node)
	}
	
	// Check for errors from iterating over rows
	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("error iterating over rows: %w", err)
	}
	
	return nodes, nil
}

// GetNodesByGeoRegion retrieves nodes by geographic region
func (c *DBClient) GetNodesByGeoRegion(geoRegion string) ([]*Node, error) {
	c.mutex.RLock()
	defer c.mutex.RUnlock()
	
	if !c.initialized {
		return nil, errors.New("database not initialized")
	}
	
	query := `
	SELECT 
		node_id, node_address, qzkp_address, public_key, reputation, first_seen, 
		last_seen, status, geo_region, node_version, is_bootstrap
	FROM nodes
	WHERE geo_region = ?
	ORDER BY last_seen DESC
	`
	
	rows, err := c.db.Query(query, geoRegion)
	if err != nil {
		return nil, fmt.Errorf("failed to get nodes by region: %w", err)
	}
	defer rows.Close()
	
	var nodes []*Node
	
	for rows.Next() {
		var node Node
		var geoRegion, nodeVersion sql.NullString
		
		err := rows.Scan(
			&node.NodeID,
			&node.NodeAddress,
			&node.QZKPAddress,
			&node.PublicKey,
			&node.Reputation,
			&node.FirstSeen,
			&node.LastSeen,
			&node.Status,
			&geoRegion,
			&nodeVersion,
			&node.IsBootstrap,
		)
		
		if err != nil {
			return nil, fmt.Errorf("failed to scan node: %w", err)
		}
		
		// Set nullable fields
		if geoRegion.Valid {
			node.GeoRegion = geoRegion.String
		}
		
		if nodeVersion.Valid {
			node.NodeVersion = nodeVersion.String
		}
		
		nodes = append(nodes, &node)
	}
	
	// Check for errors from iterating over rows
	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("error iterating over rows: %w", err)
	}
	
	return nodes, nil
}
