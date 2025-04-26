package database

import (
	"database/sql"
	"errors"
	"fmt"
	"time"
)

// CreateUser creates a new user
func (c *DBClient) CreateUser(user *User) error {
	c.mutex.Lock()
	defer c.mutex.Unlock()
	
	if !c.initialized {
		return errors.New("database not initialized")
	}
	
	query := `
	INSERT INTO users (
		user_id, username, email, role, display_name, reputation, 
		created_at, last_login, is_active, public_key
	) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
	`
	
	var email, displayName, publicKey sql.NullString
	var lastLogin sql.NullTime
	
	if user.Email != "" {
		email.Valid = true
		email.String = user.Email
	}
	
	if user.DisplayName != "" {
		displayName.Valid = true
		displayName.String = user.DisplayName
	}
	
	if user.PublicKey != "" {
		publicKey.Valid = true
		publicKey.String = user.PublicKey
	}
	
	if !user.LastLogin.IsZero() {
		lastLogin.Valid = true
		lastLogin.Time = user.LastLogin
	}
	
	_, err := c.db.Exec(
		query,
		user.UserID,
		user.Username,
		email,
		user.Role,
		displayName,
		user.Reputation,
		user.CreatedAt,
		lastLogin,
		user.IsActive,
		publicKey,
	)
	
	if err != nil {
		return fmt.Errorf("failed to create user: %w", err)
	}
	
	return nil
}

// GetUserByID retrieves a user by ID
func (c *DBClient) GetUserByID(userID string) (*User, error) {
	c.mutex.RLock()
	defer c.mutex.RUnlock()
	
	if !c.initialized {
		return nil, errors.New("database not initialized")
	}
	
	query := `
	SELECT 
		user_id, username, email, role, display_name, reputation, 
		created_at, last_login, is_active, public_key
	FROM users
	WHERE user_id = ?
	`
	
	var user User
	var email, displayName, publicKey sql.NullString
	var lastLogin sql.NullTime
	
	err := c.db.QueryRow(query, userID).Scan(
		&user.UserID,
		&user.Username,
		&email,
		&user.Role,
		&displayName,
		&user.Reputation,
		&user.CreatedAt,
		&lastLogin,
		&user.IsActive,
		&publicKey,
	)
	
	if err != nil {
		if err == sql.ErrNoRows {
			return nil, fmt.Errorf("user not found: %s", userID)
		}
		return nil, fmt.Errorf("failed to get user: %w", err)
	}
	
	// Set nullable fields
	if email.Valid {
		user.Email = email.String
	}
	
	if displayName.Valid {
		user.DisplayName = displayName.String
	}
	
	if publicKey.Valid {
		user.PublicKey = publicKey.String
	}
	
	if lastLogin.Valid {
		user.LastLogin = lastLogin.Time
	}
	
	return &user, nil
}

// GetUserByUsername retrieves a user by username
func (c *DBClient) GetUserByUsername(username string) (*User, error) {
	c.mutex.RLock()
	defer c.mutex.RUnlock()
	
	if !c.initialized {
		return nil, errors.New("database not initialized")
	}
	
	query := `
	SELECT 
		user_id, username, email, role, display_name, reputation, 
		created_at, last_login, is_active, public_key
	FROM users
	WHERE username = ?
	`
	
	var user User
	var email, displayName, publicKey sql.NullString
	var lastLogin sql.NullTime
	
	err := c.db.QueryRow(query, username).Scan(
		&user.UserID,
		&user.Username,
		&email,
		&user.Role,
		&displayName,
		&user.Reputation,
		&user.CreatedAt,
		&lastLogin,
		&user.IsActive,
		&publicKey,
	)
	
	if err != nil {
		if err == sql.ErrNoRows {
			return nil, fmt.Errorf("user not found with username: %s", username)
		}
		return nil, fmt.Errorf("failed to get user: %w", err)
	}
	
	// Set nullable fields
	if email.Valid {
		user.Email = email.String
	}
	
	if displayName.Valid {
		user.DisplayName = displayName.String
	}
	
	if publicKey.Valid {
		user.PublicKey = publicKey.String
	}
	
	if lastLogin.Valid {
		user.LastLogin = lastLogin.Time
	}
	
	return &user, nil
}

// UpdateUserLastLogin updates a user's last login time
func (c *DBClient) UpdateUserLastLogin(userID string) error {
	c.mutex.Lock()
	defer c.mutex.Unlock()
	
	if !c.initialized {
		return errors.New("database not initialized")
	}
	
	query := `
	UPDATE users SET last_login = ? WHERE user_id = ?
	`
	
	_, err := c.db.Exec(query, time.Now(), userID)
	if err != nil {
		return fmt.Errorf("failed to update user last login: %w", err)
	}
	
	return nil
}

// UpdateUserStatus updates a user's active status
func (c *DBClient) UpdateUserStatus(userID string, isActive bool) error {
	c.mutex.Lock()
	defer c.mutex.Unlock()
	
	if !c.initialized {
		return errors.New("database not initialized")
	}
	
	query := `
	UPDATE users SET is_active = ? WHERE user_id = ?
	`
	
	_, err := c.db.Exec(query, isActive, userID)
	if err != nil {
		return fmt.Errorf("failed to update user status: %w", err)
	}
	
	return nil
}

// UpdateUserReputation updates a user's reputation
func (c *DBClient) UpdateUserReputation(userID string, reputation float64) error {
	c.mutex.Lock()
	defer c.mutex.Unlock()
	
	if !c.initialized {
		return errors.New("database not initialized")
	}
	
	query := `
	UPDATE users SET reputation = ? WHERE user_id = ?
	`
	
	_, err := c.db.Exec(query, reputation, userID)
	if err != nil {
		return fmt.Errorf("failed to update user reputation: %w", err)
	}
	
	return nil
}

// ListUsers lists users with optional filtering by role
func (c *DBClient) ListUsers(role string, limit int, offset int) ([]*User, error) {
	c.mutex.RLock()
	defer c.mutex.RUnlock()
	
	if !c.initialized {
		return nil, errors.New("database not initialized")
	}
	
	var query string
	var args []interface{}
	
	if role != "" {
		query = `
		SELECT 
			user_id, username, email, role, display_name, reputation, 
			created_at, last_login, is_active, public_key
		FROM users
		WHERE role = ?
		ORDER BY created_at DESC
		LIMIT ? OFFSET ?
		`
		args = []interface{}{role, limit, offset}
	} else {
		query = `
		SELECT 
			user_id, username, email, role, display_name, reputation, 
			created_at, last_login, is_active, public_key
		FROM users
		ORDER BY created_at DESC
		LIMIT ? OFFSET ?
		`
		args = []interface{}{limit, offset}
	}
	
	rows, err := c.db.Query(query, args...)
	if err != nil {
		return nil, fmt.Errorf("failed to list users: %w", err)
	}
	defer rows.Close()
	
	var users []*User
	
	for rows.Next() {
		var user User
		var email, displayName, publicKey sql.NullString
		var lastLogin sql.NullTime
		
		err := rows.Scan(
			&user.UserID,
			&user.Username,
			&email,
			&user.Role,
			&displayName,
			&user.Reputation,
			&user.CreatedAt,
			&lastLogin,
			&user.IsActive,
			&publicKey,
		)
		
		if err != nil {
			return nil, fmt.Errorf("failed to scan user: %w", err)
		}
		
		// Set nullable fields
		if email.Valid {
			user.Email = email.String
		}
		
		if displayName.Valid {
			user.DisplayName = displayName.String
		}
		
		if publicKey.Valid {
			user.PublicKey = publicKey.String
		}
		
		if lastLogin.Valid {
			user.LastLogin = lastLogin.Time
		}
		
		users = append(users, &user)
	}
	
	// Check for errors from iterating over rows
	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("error iterating over rows: %w", err)
	}
	
	return users, nil
}

// SearchUsers searches for users by username or display name
func (c *DBClient) SearchUsers(query string, limit int) ([]*User, error) {
	c.mutex.RLock()
	defer c.mutex.RUnlock()
	
	if !c.initialized {
		return nil, errors.New("database not initialized")
	}
	
	sqlQuery := `
	SELECT 
		user_id, username, email, role, display_name, reputation, 
		created_at, last_login, is_active, public_key
	FROM users
	WHERE 
		username LIKE ? OR 
		display_name LIKE ?
	ORDER BY reputation DESC, created_at DESC
	LIMIT ?
	`
	
	searchParam := "%" + query + "%"
	
	rows, err := c.db.Query(sqlQuery, searchParam, searchParam, limit)
	if err != nil {
		return nil, fmt.Errorf("failed to search users: %w", err)
	}
	defer rows.Close()
	
	var users []*User
	
	for rows.Next() {
		var user User
		var email, displayName, publicKey sql.NullString
		var lastLogin sql.NullTime
		
		err := rows.Scan(
			&user.UserID,
			&user.Username,
			&email,
			&user.Role,
			&displayName,
			&user.Reputation,
			&user.CreatedAt,
			&lastLogin,
			&user.IsActive,
			&publicKey,
		)
		
		if err != nil {
			return nil, fmt.Errorf("failed to scan user: %w", err)
		}
		
		// Set nullable fields
		if email.Valid {
			user.Email = email.String
		}
		
		if displayName.Valid {
			user.DisplayName = displayName.String
		}
		
		if publicKey.Valid {
			user.PublicKey = publicKey.String
		}
		
		if lastLogin.Valid {
			user.LastLogin = lastLogin.Time
		}
		
		users = append(users, &user)
	}
	
	// Check for errors from iterating over rows
	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("error iterating over rows: %w", err)
	}
	
	return users, nil
}

// CreateCredential creates a new credential for a user
func (c *DBClient) CreateCredential(credential *Credential) error {
	c.mutex.Lock()
	defer c.mutex.Unlock()
	
	if !c.initialized {
		return errors.New("database not initialized")
	}
	
	query := `
	INSERT INTO credentials (
		credential_id, user_id, qzkp_proof, issued_at, expires_at, 
		credential_type, is_revoked
	) VALUES (?, ?, ?, ?, ?, ?, ?)
	`
	
	_, err := c.db.Exec(
		query,
		credential.CredentialID,
		credential.UserID,
		credential.QZKPProof,
		credential.IssuedAt,
		credential.ExpiresAt,
		credential.CredentialType,
		credential.IsRevoked,
	)
	
	if err != nil {
		return fmt.Errorf("failed to create credential: %w", err)
	}
	
	return nil
}

// GetCredentialByID retrieves a credential by ID
func (c *DBClient) GetCredentialByID(credentialID string) (*Credential, error) {
	c.mutex.RLock()
	defer c.mutex.RUnlock()
	
	if !c.initialized {
		return nil, errors.New("database not initialized")
	}
	
	query := `
	SELECT 
		credential_id, user_id, qzkp_proof, issued_at, expires_at, 
		credential_type, is_revoked
	FROM credentials
	WHERE credential_id = ?
	`
	
	var credential Credential
	
	err := c.db.QueryRow(query, credentialID).Scan(
		&credential.CredentialID,
		&credential.UserID,
		&credential.QZKPProof,
		&credential.IssuedAt,
		&credential.ExpiresAt,
		&credential.CredentialType,
		&credential.IsRevoked,
	)
	
	if err != nil {
		if err == sql.ErrNoRows {
			return nil, fmt.Errorf("credential not found: %s", credentialID)
		}
		return nil, fmt.Errorf("failed to get credential: %w", err)
	}
	
	return &credential, nil
}

// GetCredentialsByUserID retrieves credentials for a user
func (c *DBClient) GetCredentialsByUserID(userID string) ([]*Credential, error) {
	c.mutex.RLock()
	defer c.mutex.RUnlock()
	
	if !c.initialized {
		return nil, errors.New("database not initialized")
	}
	
	query := `
	SELECT 
		credential_id, user_id, qzkp_proof, issued_at, expires_at, 
		credential_type, is_revoked
	FROM credentials
	WHERE user_id = ?
	ORDER BY issued_at DESC
	`
	
	rows, err := c.db.Query(query, userID)
	if err != nil {
		return nil, fmt.Errorf("failed to get credentials: %w", err)
	}
	defer rows.Close()
	
	var credentials []*Credential
	
	for rows.Next() {
		var credential Credential
		
		err := rows.Scan(
			&credential.CredentialID,
			&credential.UserID,
			&credential.QZKPProof,
			&credential.IssuedAt,
			&credential.ExpiresAt,
			&credential.CredentialType,
			&credential.IsRevoked,
		)
		
		if err != nil {
			return nil, fmt.Errorf("failed to scan credential: %w", err)
		}
		
		credentials = append(credentials, &credential)
	}
	
	// Check for errors from iterating over rows
	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("error iterating over rows: %w", err)
	}
	
	return credentials, nil
}

// RevokeCredential revokes a credential
func (c *DBClient) RevokeCredential(credentialID string) error {
	c.mutex.Lock()
	defer c.mutex.Unlock()
	
	if !c.initialized {
		return errors.New("database not initialized")
	}
	
	query := `
	UPDATE credentials SET is_revoked = true WHERE credential_id = ?
	`
	
	_, err := c.db.Exec(query, credentialID)
	if err != nil {
		return fmt.Errorf("failed to revoke credential: %w", err)
	}
	
	return nil
}

// GetActiveUserCredentials retrieves active (non-expired, non-revoked) credentials for a user
func (c *DBClient) GetActiveUserCredentials(userID string) ([]*Credential, error) {
	c.mutex.RLock()
	defer c.mutex.RUnlock()
	
	if !c.initialized {
		return nil, errors.New("database not initialized")
	}
	
	query := `
	SELECT 
		credential_id, user_id, qzkp_proof, issued_at, expires_at, 
		credential_type, is_revoked
	FROM credentials
	WHERE 
		user_id = ? AND 
		is_revoked = false AND 
		expires_at > ?
	ORDER BY issued_at DESC
	`
	
	rows, err := c.db.Query(query, userID, time.Now())
	if err != nil {
		return nil, fmt.Errorf("failed to get active credentials: %w", err)
	}
	defer rows.Close()
	
	var credentials []*Credential
	
	for rows.Next() {
		var credential Credential
		
		err := rows.Scan(
			&credential.CredentialID,
			&credential.UserID,
			&credential.QZKPProof,
			&credential.IssuedAt,
			&credential.ExpiresAt,
			&credential.CredentialType,
			&credential.IsRevoked,
		)
		
		if err != nil {
			return nil, fmt.Errorf("failed to scan credential: %w", err)
		}
		
		credentials = append(credentials, &credential)
	}
	
	// Check for errors from iterating over rows
	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("error iterating over rows: %w", err)
	}
	
	return credentials, nil
}
