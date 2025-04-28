#!/bin/bash
# Script to run the complete GDELT news analysis system with PostgreSQL

# Default variables
CONFIG_PATH="config/database.json"
CHUNKS_DIR="analysis_gdelt_chunks/chunks"
OUTPUT_DIR="analysis_gdelt_chunks"
DATASET_DIR="dataset_gdelt_enhanced"
MODELS_DIR="analysis_gdelt_chunks/models"
DASHBOARD_PORT=5006
CHUNK_DELAY=20
OPTIMIZATION_INTERVAL=300
LEARNING_INTERVAL=600
FETCH_INTERVAL=3600
ARTICLES_PER_FETCH=500
CHUNK_SIZE=100
CPU_LIMIT=50

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --port)
            DASHBOARD_PORT="$2"
            shift 2
            ;;
        --config-path)
            CONFIG_PATH="$2"
            shift 2
            ;;
        --chunk-delay)
            CHUNK_DELAY="$2"
            shift 2
            ;;
        --cpu-limit)
            CPU_LIMIT="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Load database configuration
if [ -f "$CONFIG_PATH" ]; then
    echo "Loading database configuration from $CONFIG_PATH"
    # Extract values from JSON using jq if available
    if command -v jq &> /dev/null; then
        POSTGRES_HOST=$(jq -r '.postgres.host' "$CONFIG_PATH")
        POSTGRES_PORT=$(jq -r '.postgres.port' "$CONFIG_PATH")
        POSTGRES_DB=$(jq -r '.postgres.dbname' "$CONFIG_PATH")
        POSTGRES_USER=$(jq -r '.postgres.user' "$CONFIG_PATH")
        POSTGRES_PASSWORD=$(jq -r '.postgres.password' "$CONFIG_PATH")

        # Set environment variables
        export POSTGRES_HOST="$POSTGRES_HOST"
        export POSTGRES_PORT="$POSTGRES_PORT"
        export POSTGRES_DB="$POSTGRES_DB"
        export POSTGRES_USER="$POSTGRES_USER"
        export POSTGRES_PASSWORD="$POSTGRES_PASSWORD"

        echo "Using PostgreSQL database: $POSTGRES_DB on $POSTGRES_HOST:$POSTGRES_PORT"
    else
        echo "jq not found, using default PostgreSQL configuration"
        export POSTGRES_HOST="localhost"
        export POSTGRES_PORT="5432"
        export POSTGRES_DB="gdelt_news"
        export POSTGRES_USER="postgres"
        export POSTGRES_PASSWORD="adv62062"
    fi
else
    echo "Database configuration file not found, using default PostgreSQL configuration"
    export POSTGRES_HOST="localhost"
    export POSTGRES_PORT="5432"
    export POSTGRES_DB="gdelt_news"
    export POSTGRES_USER="postgres"
    export POSTGRES_PASSWORD="adv62062"
fi

# Create directories if they don't exist
mkdir -p "$CHUNKS_DIR"
mkdir -p "$OUTPUT_DIR/entity_lists"
mkdir -p "$DATASET_DIR"
mkdir -p "$MODELS_DIR"

# Activate virtual environment
source venv/bin/activate

# Install psutil if not already installed
pip install psycopg2-binary gdeltdoc --quiet

# Function to clean up processes on exit
cleanup() {
    echo "Cleaning up processes..."

    # Kill dashboard process
    if [ -n "$DASHBOARD_PID" ]; then
        echo "Stopping dashboard (PID: $DASHBOARD_PID)..."
        kill -TERM "$DASHBOARD_PID" 2>/dev/null
    fi

    # Kill chunk processor
    if [ -n "$CHUNK_PROCESSOR_PID" ]; then
        echo "Stopping chunk processor (PID: $CHUNK_PROCESSOR_PID)..."
        kill -TERM "$CHUNK_PROCESSOR_PID" 2>/dev/null
    fi

    # Kill optimization daemon
    if [ -n "$OPTIMIZATION_PID" ]; then
        echo "Stopping optimization daemon (PID: $OPTIMIZATION_PID)..."
        kill -TERM "$OPTIMIZATION_PID" 2>/dev/null
    fi

    # Kill fetcher daemon
    if [ -n "$FETCHER_PID" ]; then
        echo "Stopping fetcher daemon (PID: $FETCHER_PID)..."
        kill -TERM "$FETCHER_PID" 2>/dev/null
    fi

    # Kill learning daemon
    if [ -n "$LEARNING_PID" ]; then
        echo "Stopping learning daemon (PID: $LEARNING_PID)..."
        kill -TERM "$LEARNING_PID" 2>/dev/null
    fi

    echo "All processes stopped"
    exit 0
}

# Set up trap for clean exit
trap cleanup SIGINT SIGTERM

# Start the dashboard in the background
echo "Starting the dashboard on port $DASHBOARD_PORT..."
python dashboard_postgres.py --port "$DASHBOARD_PORT" --config-path "$CONFIG_PATH" &
DASHBOARD_PID=$!

# Wait for the dashboard to start
echo "Waiting for the dashboard to start..."
sleep 5

# Open the dashboard in the browser
echo "Opening the dashboard in the browser..."
python -c "import webbrowser; webbrowser.open('http://127.0.0.1:$DASHBOARD_PORT')"

# Start the optimization daemon in the background
echo "Starting the optimization daemon (CPU limit: $CPU_LIMIT%)..."
python -m python.src.gdelt.analyzer.optimization_daemon --config-path "$CONFIG_PATH" --interval "$OPTIMIZATION_INTERVAL" --entity-lists-path "$OUTPUT_DIR/entity_lists" &
OPTIMIZATION_PID=$!

# Start the enhanced fetcher in the background
echo "Starting the enhanced GDELT fetcher..."
python enhanced_gdelt_fetcher.py --config-path "$CONFIG_PATH" --days-back 30 --articles-per-day "$ARTICLES_PER_FETCH" --workers 4 &
FETCHER_PID=$!

# Start the continuous learning daemon in the background
echo "Starting the continuous learning daemon (CPU limit: $CPU_LIMIT%)..."
python -m python.src.gdelt.analyzer.continuous_learning_daemon --config-path "$CONFIG_PATH" --models-dir "$MODELS_DIR" --interval "$LEARNING_INTERVAL" --cpu-limit "$CPU_LIMIT" &
LEARNING_PID=$!

# Start processing chunks in the background
echo "Starting to process chunks with a delay of $CHUNK_DELAY seconds..."
python process_all_chunks_postgres.py --chunks-dir "$CHUNKS_DIR" --config-path "$CONFIG_PATH" --output-dir "$OUTPUT_DIR" --delay "$CHUNK_DELAY" &
CHUNK_PROCESSOR_PID=$!

# Print status
echo "System is running:"
echo "- Dashboard: http://127.0.0.1:$DASHBOARD_PORT (PID: $DASHBOARD_PID)"
echo "- Chunk Processor (PID: $CHUNK_PROCESSOR_PID)"
echo "- Optimization Daemon (PID: $OPTIMIZATION_PID)"
echo "- Enhanced GDELT Fetcher (PID: $FETCHER_PID)"
echo "- Continuous Learning Daemon (PID: $LEARNING_PID)"
echo "- CPU Usage Limit: $CPU_LIMIT%"
echo "Press Ctrl+C to stop all components"

# Wait for any process to exit
wait -n

# Clean up other processes
cleanup
