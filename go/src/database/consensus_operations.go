package database

import (
	"database/sql"
	"errors"
	"fmt"
	"time"
)

// CreateConsensusLog creates a new consensus log entry
func (c *DBClient) CreateConsensusLog(log *ConsensusLog) error {
	c.mutex.Lock()
	defer c.mutex.Unlock()
	
	if !c.initialized {
		return errors.New("database not initialized")
	}
	
	query := `
	INSERT INTO consensus_logs (
		log_id, round_id, node_id, log_time, action, status, details
	) VALUES (?, ?, ?, ?, ?, ?, ?)
	`
	
	var details sql.NullString
	
	if log.Details != "" {
		details.Valid = true
		details.String = log.Details
	}
	
	_, err := c.db.Exec(
		query,
		log.LogID,
		log.RoundID,
		log.NodeID,
		log.LogTime,
		log.Action,
		log.Status,
		details,
	)
	
	if err != nil {
		return fmt.Errorf("failed to create consensus log: %w", err)
	}
	
	return nil
}

// GetConsensusLogsByRound retrieves consensus logs for a specific round
func (c *DBClient) GetConsensusLogsByRound(roundID string) ([]*ConsensusLog, error) {
	c.mutex.RLock()
	defer c.mutex.RUnlock()
	
	if !c.initialized {
		return nil, errors.New("database not initialized")
	}
	
	query := `
	SELECT 
		log_id, round_id, node_id, log_time, action, status, details
	FROM consensus_logs
	WHERE round_id = ?
	ORDER BY log_time ASC
	`
	
	rows, err := c.db.Query(query, roundID)
	if err != nil {
		return nil, fmt.Errorf("failed to get consensus logs: %w", err)
	}
	defer rows.Close()
	
	var logs []*ConsensusLog
	
	for rows.Next() {
		var log ConsensusLog
		var details sql.NullString
		
		err := rows.Scan(
			&log.LogID,
			&log.RoundID,
			&log.NodeID,
			&log.LogTime,
			&log.Action,
			&log.Status,
			&details,
		)
		
		if err != nil {
			return nil, fmt.Errorf("failed to scan consensus log: %w", err)
		}
		
		// Set nullable fields
		if details.Valid {
			log.Details = details.String
		}
		
		logs = append(logs, &log)
	}
	
	// Check for errors from iterating over rows
	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("error iterating over rows: %w", err)
	}
	
	return logs, nil
}

// GetConsensusLogsByNode retrieves consensus logs for a specific node
func (c *DBClient) GetConsensusLogsByNode(nodeID string, limit int) ([]*ConsensusLog, error) {
	c.mutex.RLock()
	defer c.mutex.RUnlock()
	
	if !c.initialized {
		return nil, errors.New("database not initialized")
	}
	
	query := `
	SELECT 
		log_id, round_id, node_id, log_time, action, status, details
	FROM consensus_logs
	WHERE node_id = ?
	ORDER BY log_time DESC
	LIMIT ?
	`
	
	rows, err := c.db.Query(query, nodeID, limit)
	if err != nil {
		return nil, fmt.Errorf("failed to get consensus logs: %w", err)
	}
	defer rows.Close()
	
	var logs []*ConsensusLog
	
	for rows.Next() {
		var log ConsensusLog
		var details sql.NullString
		
		err := rows.Scan(
			&log.LogID,
			&log.RoundID,
			&log.NodeID,
			&log.LogTime,
			&log.Action,
			&log.Status,
			&details,
		)
		
		if err != nil {
			return nil, fmt.Errorf("failed to scan consensus log: %w", err)
		}
		
		// Set nullable fields
		if details.Valid {
			log.Details = details.String
		}
		
		logs = append(logs, &log)
	}
	
	// Check for errors from iterating over rows
	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("error iterating over rows: %w", err)
	}
	
	return logs, nil
}

// GetRecentConsensusLogs retrieves recent consensus logs
func (c *DBClient) GetRecentConsensusLogs(limit int) ([]*ConsensusLog, error) {
	c.mutex.RLock()
	defer c.mutex.RUnlock()
	
	if !c.initialized {
		return nil, errors.New("database not initialized")
	}
	
	query := `
	SELECT 
		log_id, round_id, node_id, log_time, action, status, details
	FROM consensus_logs
	ORDER BY log_time DESC
	LIMIT ?
	`
	
	rows, err := c.db.Query(query, limit)
	if err != nil {
		return nil, fmt.Errorf("failed to get recent consensus logs: %w", err)
	}
	defer rows.Close()
	
	var logs []*ConsensusLog
	
	for rows.Next() {
		var log ConsensusLog
		var details sql.NullString
		
		err := rows.Scan(
			&log.LogID,
			&log.RoundID,
			&log.NodeID,
			&log.LogTime,
			&log.Action,
			&log.Status,
			&details,
		)
		
		if err != nil {
			return nil, fmt.Errorf("failed to scan consensus log: %w", err)
		}
		
		// Set nullable fields
		if details.Valid {
			log.Details = details.String
		}
		
		logs = append(logs, &log)
	}
	
	// Check for errors from iterating over rows
	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("error iterating over rows: %w", err)
	}
	
	return logs, nil
}

// GetConsensusLogsByAction retrieves consensus logs for a specific action
func (c *DBClient) GetConsensusLogsByAction(action string, limit int) ([]*ConsensusLog, error) {
	c.mutex.RLock()
	defer c.mutex.RUnlock()
	
	if !c.initialized {
		return nil, errors.New("database not initialized")
	}
	
	query := `
	SELECT 
		log_id, round_id, node_id, log_time, action, status, details
	FROM consensus_logs
	WHERE action = ?
	ORDER BY log_time DESC
	LIMIT ?
	`
	
	rows, err := c.db.Query(query, action, limit)
	if err != nil {
		return nil, fmt.Errorf("failed to get consensus logs by action: %w", err)
	}
	defer rows.Close()
	
	var logs []*ConsensusLog
	
	for rows.Next() {
		var log ConsensusLog
		var details sql.NullString
		
		err := rows.Scan(
			&log.LogID,
			&log.RoundID,
			&log.NodeID,
			&log.LogTime,
			&log.Action,
			&log.Status,
			&details,
		)
		
		if err != nil {
			return nil, fmt.Errorf("failed to scan consensus log: %w", err)
		}
		
		// Set nullable fields
		if details.Valid {
			log.Details = details.String
		}
		
		logs = append(logs, &log)
	}
	
	// Check for errors from iterating over rows
	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("error iterating over rows: %w", err)
	}
	
	return logs, nil
}

// CreateSystemEvent creates a new system event
func (c *DBClient) CreateSystemEvent(event *SystemEvent) error {
	c.mutex.Lock()
	defer c.mutex.Unlock()
	
	if !c.initialized {
		return errors.New("database not initialized")
	}
	
	query := `
	INSERT INTO system_events (
		event_id, event_type, event_time, severity, details, node_id
	) VALUES (?, ?, ?, ?, ?, ?)
	`
	
	var details, nodeID sql.NullString
	
	if event.Details != "" {
		details.Valid = true
		details.String = event.Details
	}
	
	if event.NodeID != "" {
		nodeID.Valid = true
		nodeID.String = event.NodeID
	}
	
	_, err := c.db.Exec(
		query,
		event.EventID,
		event.EventType,
		event.EventTime,
		event.Severity,
		details,
		nodeID,
	)
	
	if err != nil {
		return fmt.Errorf("failed to create system event: %w", err)
	}
	
	return nil
}

// GetRecentSystemEvents retrieves recent system events
func (c *DBClient) GetRecentSystemEvents(limit int) ([]*SystemEvent, error) {
	c.mutex.RLock()
	defer c.mutex.RUnlock()
	
	if !c.initialized {
		return nil, errors.New("database not initialized")
	}
	
	query := `
	SELECT 
		event_id, event_type, event_time, severity, details, node_id
	FROM system_events
	ORDER BY event_time DESC
	LIMIT ?
	`
	
	rows, err := c.db.Query(query, limit)
	if err != nil {
		return nil, fmt.Errorf("failed to get recent system events: %w", err)
	}
	defer rows.Close()
	
	var events []*SystemEvent
	
	for rows.Next() {
		var event SystemEvent
		var details, nodeID sql.NullString
		
		err := rows.Scan(
			&event.EventID,
			&event.EventType,
			&event.EventTime,
			&event.Severity,
			&details,
			&nodeID,
		)
		
		if err != nil {
			return nil, fmt.Errorf("failed to scan system event: %w", err)
		}
		
		// Set nullable fields
		if details.Valid {
			event.Details = details.String
		}
		
		if nodeID.Valid {
			event.NodeID = nodeID.String
		}
		
		events = append(events, &event)
	}
	
	// Check for errors from iterating over rows
	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("error iterating over rows: %w", err)
	}
	
	return events, nil
}

// GetSystemEventsBySeverity retrieves system events by severity
func (c *DBClient) GetSystemEventsBySeverity(severity string, limit int) ([]*SystemEvent, error) {
	c.mutex.RLock()
	defer c.mutex.RUnlock()
	
	if !c.initialized {
		return nil, errors.New("database not initialized")
	}
	
	query := `
	SELECT 
		event_id, event_type, event_time, severity, details, node_id
	FROM system_events
	WHERE severity = ?
	ORDER BY event_time DESC
	LIMIT ?
	`
	
	rows, err := c.db.Query(query, severity, limit)
	if err != nil {
		return nil, fmt.Errorf("failed to get system events by severity: %w", err)
	}
	defer rows.Close()
	
	var events []*SystemEvent
	
	for rows.Next() {
		var event SystemEvent
		var details, nodeID sql.NullString
		
		err := rows.Scan(
			&event.EventID,
			&event.EventType,
			&event.EventTime,
			&event.Severity,
			&details,
			&nodeID,
		)
		
		if err != nil {
			return nil, fmt.Errorf("failed to scan system event: %w", err)
		}
		
		// Set nullable fields
		if details.Valid {
			event.Details = details.String
		}
		
		if nodeID.Valid {
			event.NodeID = nodeID.String
		}
		
		events = append(events, &event)
	}
	
	// Check for errors from iterating over rows
	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("error iterating over rows: %w", err)
	}
	
	return events, nil
}
