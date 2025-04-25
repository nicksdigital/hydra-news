package database

import (
	"database/sql"
	"errors"
	"fmt"
	"log"
	"sync"
	"time"
	
	_ "github.com/mattn/go-sqlite3" // SQLite driver
)

// DBClient provides a client for interacting with the database
type DBClient struct {
	db           *sql.DB
	dbPath       string
	initialized  bool
	backupConfig BackupConfig
	mutex        sync.RWMutex
}

// BackupConfig defines the configuration for database backups
type BackupConfig struct {
	BackupDir       string
	BackupInterval  time.Duration
	MaxBackups      int
	EnableAutomatic bool
}

// DefaultBackupConfig creates a default backup configuration
func DefaultBackupConfig() BackupConfig {
	return BackupConfig{
		BackupDir:       "./backups",
		BackupInterval:  24 * time.Hour,
		MaxBackups:      7,
		EnableAutomatic: true,
	}
}

// NewDBClient creates a new database client
func NewDBClient(dbPath string) (*DBClient, error) {
	client := &DBClient{
		dbPath:       dbPath,
		backupConfig: DefaultBackupConfig(),
	}
	
	return client, nil
}

// Initialize initializes the database
func (c *DBClient) Initialize() error {
	c.mutex.Lock()
	defer c.mutex.Unlock()
	
	if c.initialized {
		return nil // Already initialized
	}
	
	var err error
	
	// Open database connection
	c.db, err = sql.Open("sqlite3", c.dbPath)
	if err != nil {
		return fmt.Errorf("failed to open database: %w", err)
	}
	
	// Set connection parameters
	c.db.SetMaxOpenConns(10)
	c.db.SetMaxIdleConns(5)
	c.db.SetConnMaxLifetime(30 * time.Minute)
	
	// Test connection
	if err := c.db.Ping(); err != nil {
		c.db.Close()
		return fmt.Errorf("failed to ping database: %w", err)
	}
	
	// Create tables
	if err := c.createTables(); err != nil {
		c.db.Close()
		return fmt.Errorf("failed to create tables: %w", err)
	}
	
	// Start automatic backup if enabled
	if c.backupConfig.EnableAutomatic {
		go c.startAutomaticBackups()
	}
	
	c.initialized = true
	log.Printf("Database initialized: %s", c.dbPath)
	
	return nil
}

// Close closes the database connection
func (c *DBClient) Close() error {
	c.mutex.Lock()
	defer c.mutex.Unlock()
	
	if !c.initialized {
		return nil // Not initialized
	}
	
	if err := c.db.Close(); err != nil {
		return fmt.Errorf("failed to close database: %w", err)
	}
	
	c.initialized = false
	return nil
}

// SetBackupConfig sets the backup configuration
func (c *DBClient) SetBackupConfig(config BackupConfig) {
	c.mutex.Lock()
	defer c.mutex.Unlock()
	
	c.backupConfig = config
}

// CreateBackup creates a database backup
func (c *DBClient) CreateBackup(backupPath string) error {
	c.mutex.Lock()
	defer c.mutex.Unlock()
	
	if !c.initialized {
		return errors.New("database not initialized")
	}
	
	// In a real implementation, this would create a backup of the database
	// For this simplified version, we'll just log the action
	log.Printf("Creating database backup to: %s", backupPath)
	
	return nil
}

// RestoreBackup restores a database from backup
func (c *DBClient) RestoreBackup(backupPath string) error {
	c.mutex.Lock()
	defer c.mutex.Unlock()
	
	// In a real implementation, this would restore the database from a backup
	// For this simplified version, we'll just log the action
	log.Printf("Restoring database from backup: %s", backupPath)
	
	return nil
}

// createTables creates the database tables
func (c *DBClient) createTables() error {
	// Get all table schemas
	schemas := GetAllSchemas()
	
	// Execute each schema
	for _, schema := range schemas {
		_, err := c.db.Exec(schema)
		if err != nil {
			return fmt.Errorf("failed to create table: %w", err)
		}
	}
	
	return nil
}

// startAutomaticBackups starts the automatic backup process
func (c *DBClient) startAutomaticBackups() {
	ticker := time.NewTicker(c.backupConfig.BackupInterval)
	defer ticker.Stop()
	
	for {
		<-ticker.C
		
		// Create backup filename with timestamp
		backupPath := fmt.Sprintf("%s/backup_%s.db", c.backupConfig.BackupDir, time.Now().Format("20060102_150405"))
		
		// Create backup
		err := c.CreateBackup(backupPath)
		if err != nil {
			log.Printf("Failed to create automatic backup: %v", err)
		} else {
			log.Printf("Automatic backup created: %s", backupPath)
		}
		
		// Clean old backups
		c.cleanOldBackups()
	}
}

// cleanOldBackups removes old backups exceeding the maximum count
func (c *DBClient) cleanOldBackups() {
	// In a real implementation, this would:
	// 1. List all backup files in the backup directory
	// 2. Sort them by creation time
	// 3. Delete the oldest ones if count exceeds MaxBackups
	
	// For this simplified version, we'll just log the action
	log.Printf("Cleaning old backups, keeping at most %d", c.backupConfig.MaxBackups)
}

// Transaction begins a new database transaction
func (c *DBClient) Transaction() (*sql.Tx, error) {
	if !c.initialized {
		return nil, errors.New("database not initialized")
	}
	
	return c.db.Begin()
}
