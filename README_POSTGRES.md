# PostgreSQL Setup for GDELT News Analysis

This document explains how to set up and use PostgreSQL with the GDELT News Analysis system.

## Why PostgreSQL?

While the system works with SQLite, PostgreSQL offers several advantages:

1. **Concurrent Access**: PostgreSQL handles multiple processes accessing the database simultaneously, eliminating the "database is locked" errors.
2. **Better Performance**: PostgreSQL is optimized for larger datasets and complex queries.
3. **Scalability**: PostgreSQL can handle much larger datasets than SQLite.
4. **Advanced Features**: PostgreSQL offers advanced features like full-text search, JSON support, and more.

## Prerequisites

1. PostgreSQL installed on your system (version 10 or higher recommended)
2. Python 3.7 or higher
3. `psycopg2` Python package (installed automatically by the setup script)

## Setup Instructions

### 1. Install Required Dependencies

First, install the required Python packages and PostgreSQL client tools:

```bash
./install_postgres_deps.sh
```

This script will:
- Install the required Python packages (`psycopg2-binary`, `pandas`, `tqdm`, etc.)
- Install PostgreSQL client tools if not already installed
- Install `jq` for JSON parsing in shell scripts
- Download NLTK data

### 2. Install PostgreSQL Server

#### On Ubuntu/Debian:
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
```

#### On macOS (using Homebrew):
```bash
brew install postgresql
brew services start postgresql
```

#### On Windows:
Download and install from [PostgreSQL website](https://www.postgresql.org/download/windows/)

### 3. Create a PostgreSQL User and Database

You can use the default PostgreSQL user (`postgres`) or create a new user:

```bash
sudo -u postgres createuser --interactive
sudo -u postgres createdb gdelt_news
```

Or use the provided setup script:

```bash
./setup_postgres.sh
```

### 4. Configure the System to Use PostgreSQL

Run the setup script with your PostgreSQL credentials:

```bash
./setup_postgres.sh --host localhost --port 5432 --db gdelt_news --user postgres --password your_password
```

This will:
- Create a configuration file at `config/database.json`
- Initialize the PostgreSQL database with the required tables
- Create a `.env` file with the database configuration

## Using PostgreSQL

Once configured, the system will automatically use PostgreSQL instead of SQLite. You can run the system as usual:

```bash
./run_complete_system.sh
```

## Switching Between PostgreSQL and SQLite

You can switch between PostgreSQL and SQLite by editing the `config/database.json` file:

```json
{
  "use_postgres": true,  // Set to false to use SQLite
  "postgres": {
    "host": "localhost",
    "port": 5432,
    "dbname": "gdelt_news",
    "user": "postgres",
    "password": "postgres",
    "min_conn": 1,
    "max_conn": 10
  },
  "sqlite": {
    "db_path": "analysis_gdelt_chunks/gdelt_news.db"
  }
}
```

Or by setting environment variables:

```bash
# Use PostgreSQL
export GDELT_DB_TYPE=postgres
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_DB=gdelt_news
export POSTGRES_USER=postgres
export POSTGRES_PASSWORD=your_password

# Use SQLite
export GDELT_DB_TYPE=sqlite
export SQLITE_DB_PATH=analysis_gdelt_chunks/gdelt_news.db
```

## Troubleshooting

### Connection Issues

If you encounter connection issues, check:

1. PostgreSQL service is running:
   ```bash
   sudo systemctl status postgresql  # On Linux
   brew services list                # On macOS
   ```

2. PostgreSQL user has the correct permissions:
   ```bash
   sudo -u postgres psql -c "ALTER USER postgres WITH PASSWORD 'your_password';"
   sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE gdelt_news TO postgres;"
   ```

3. PostgreSQL is configured to accept connections:
   Edit `pg_hba.conf` to allow connections from your application.

### Database Migration

To migrate data from SQLite to PostgreSQL, use the provided migration script:

```bash
python -m python.src.gdelt.database.migrate_sqlite_to_postgres --sqlite-path analysis_gdelt_chunks/gdelt_news.db
```

## Performance Tuning

For better performance with large datasets:

1. Increase the connection pool size in `config/database.json`:
   ```json
   "postgres": {
     "min_conn": 5,
     "max_conn": 20
   }
   ```

2. Adjust PostgreSQL configuration for your hardware:
   - `shared_buffers`: 25% of available RAM
   - `work_mem`: 32-64MB for complex queries
   - `maintenance_work_mem`: 256MB for maintenance operations
   - `effective_cache_size`: 75% of available RAM
