# Hydra News Database Implementation

This package provides a SQLite-based database implementation for the Hydra News system. It handles persistent storage of news content, entities, claims, verifications, users, credentials, sources, consensus logs, and system events.

## Features

- **Thread-safe**: All database operations are thread-safe with proper mutex locking
- **Modular design**: Separate files for different types of operations
- **Automatic backups**: Configurable automatic backup system
- **Transaction support**: Support for atomic operations via transactions

## Main Components

- **DB Client**: Central database client that manages connections and operations
- **Schema**: Database schema definitions for all tables
- **Models**: Go structs representing database entities
- **Operations**: Functions to interact with the database, separated by domain:
  - Content operations
  - Entity and claim operations
  - Verification operations
  - Node operations
  - Consensus operations
  - User operations
  - Source operations

## Usage

```go
// Create a new database client
dbClient, err := database.NewDBClient("hydra_news.db")
if err != nil {
    log.Fatalf("Failed to create database client: %v", err)
}

// Initialize the database
if err := dbClient.Initialize(); err != nil {
    log.Fatalf("Failed to initialize database: %v", err)
}

// Use the database client
content, err := dbClient.GetNewsContent(contentHash)
if err != nil {
    log.Printf("Error retrieving content: %v", err)
}

// Close the database connection when done
defer dbClient.Close()
```

## Error Handling

All database operations return errors when they fail, which should be handled appropriately by the caller. Common error patterns include:

- Database not initialized
- Item not found
- Query execution errors
- Transaction errors

## Backup System

The database client includes a configurable backup system:

```go
// Configure backup settings
dbClient.SetBackupConfig(database.BackupConfig{
    BackupDir:       "./backups",
    BackupInterval:  12 * time.Hour,
    MaxBackups:      10,
    EnableAutomatic: true,
})

// Create manual backup
err := dbClient.CreateBackup("manual_backup.db")
if err != nil {
    log.Printf("Backup failed: %v", err)
}
```

## Transactions

For operations that need to be atomic, use the transaction support:

```go
// Begin a transaction
tx, err := dbClient.Transaction()
if err != nil {
    return err
}

// Defer a rollback in case of error
defer func() {
    if err != nil {
        tx.Rollback()
    }
}()

// Perform operations in the transaction
// ...

// Commit the transaction if everything succeeded
if err = tx.Commit(); err != nil {
    return err
}
```
