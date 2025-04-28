#!/bin/bash
# Script to reset PostgreSQL database

# Load configuration from .env if it exists
if [ -f ".env" ]; then
    source .env
fi

# Default values
POSTGRES_HOST=${POSTGRES_HOST:-"localhost"}
POSTGRES_PORT=${POSTGRES_PORT:-5432}
POSTGRES_DB=${POSTGRES_DB:-"gdelt_news"}
POSTGRES_USER=${POSTGRES_USER:-"postgres"}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-"adv62062"}

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
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Activate virtual environment
source venv/bin/activate

# Reset PostgreSQL database
echo "Resetting PostgreSQL database..."
python -m python.src.gdelt.database.postgres_adapter --host "$POSTGRES_HOST" --port "$POSTGRES_PORT" --dbname "$POSTGRES_DB" --user "$POSTGRES_USER" --password "$POSTGRES_PASSWORD" --reset

echo "PostgreSQL database reset completed"
