#!/bin/bash
# Script to set up PostgreSQL for GDELT News Analysis

# Default values
POSTGRES_HOST="localhost"
POSTGRES_PORT=5432
POSTGRES_DB="gdelt_news"
POSTGRES_USER="postgres"
POSTGRES_PASSWORD="adv62062"
ADMIN_USER="postgres"
ADMIN_PASSWORD="adv62062"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --host)
      POSTGRES_HOST="$2"
      shift 2
      ;;
    --port)
      POSTGRES_PORT="$2"
      shift 2
      ;;
    --db)
      POSTGRES_DB="$2"
      shift 2
      ;;
    --user)
      POSTGRES_USER="$2"
      shift 2
      ;;
    --password)
      POSTGRES_PASSWORD="$2"
      shift 2
      ;;
    --admin-user)
      ADMIN_USER="$2"
      shift 2
      ;;
    --admin-password)
      ADMIN_PASSWORD="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Activate virtual environment
source venv/bin/activate

# Create configuration directory
mkdir -p config

# Save database configuration
cat > config/database.json << EOL
{
  "use_postgres": true,
  "postgres": {
    "host": "${POSTGRES_HOST}",
    "port": ${POSTGRES_PORT},
    "dbname": "${POSTGRES_DB}",
    "user": "${POSTGRES_USER}",
    "password": "${POSTGRES_PASSWORD}",
    "min_conn": 1,
    "max_conn": 10
  },
  "sqlite": {
    "db_path": "analysis_gdelt_chunks/gdelt_news.db"
  }
}
EOL

echo "Saved database configuration to config/database.json"

# Set environment variables for PostgreSQL
export POSTGRES_HOST="${POSTGRES_HOST}"
export POSTGRES_PORT="${POSTGRES_PORT}"
export POSTGRES_DB="${POSTGRES_DB}"
export POSTGRES_USER="${POSTGRES_USER}"
export POSTGRES_PASSWORD="${POSTGRES_PASSWORD}"

# Initialize PostgreSQL database
echo "Initializing PostgreSQL database..."
python -m python.src.gdelt.database.init_postgres \
  --host "${POSTGRES_HOST}" \
  --port "${POSTGRES_PORT}" \
  --admin-user "${ADMIN_USER}" \
  --admin-password "${ADMIN_PASSWORD}" \
  --user "${POSTGRES_USER}" \
  --password "${POSTGRES_PASSWORD}" \
  --dbname "${POSTGRES_DB}" \
  --all

echo "PostgreSQL setup completed"

# Create a .env file for easy loading of environment variables
cat > .env << EOL
# PostgreSQL configuration
GDELT_DB_TYPE=postgres
POSTGRES_HOST=${POSTGRES_HOST}
POSTGRES_PORT=${POSTGRES_PORT}
POSTGRES_DB=${POSTGRES_DB}
POSTGRES_USER=${POSTGRES_USER}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
EOL

echo "Created .env file with database configuration"
echo "To load environment variables, run: source .env"
