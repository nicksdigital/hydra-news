#!/bin/bash
# Script to run the enhanced GDELT fetcher as a daemon

# Configuration
CONFIG_PATH="config/database.json"
DAYS_BACK=30
ARTICLES_PER_DAY=10000
WORKERS=4
LOG_FILE="logs/gdelt_fetcher.log"
PID_FILE="logs/gdelt_fetcher.pid"
FETCH_INTERVAL=3600  # 1 hour in seconds
CPU_LIMIT=50  # CPU usage limit in percentage

# Create logs directory if it doesn't exist
mkdir -p logs

# Function to check if the daemon is already running
is_running() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null; then
            return 0  # Running
        fi
    fi
    return 1  # Not running
}

# Function to start the daemon
start_daemon() {
    if is_running; then
        echo "GDELT fetcher daemon is already running (PID: $(cat "$PID_FILE"))"
        return
    fi
    
    echo "Starting GDELT fetcher daemon..."
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Run the daemon in the background
    while true; do
        echo "$(date): Starting GDELT fetch cycle" >> "$LOG_FILE"
        
        # Run the enhanced fetcher with CPU limit
        if command -v cpulimit > /dev/null; then
            cpulimit -l "$CPU_LIMIT" -f python enhanced_gdelt_fetcher.py \
                --config-path "$CONFIG_PATH" \
                --days-back "$DAYS_BACK" \
                --articles-per-day "$ARTICLES_PER_DAY" \
                --workers "$WORKERS" >> "$LOG_FILE" 2>&1
        else
            python enhanced_gdelt_fetcher.py \
                --config-path "$CONFIG_PATH" \
                --days-back "$DAYS_BACK" \
                --articles-per-day "$ARTICLES_PER_DAY" \
                --workers "$WORKERS" >> "$LOG_FILE" 2>&1
        fi
        
        echo "$(date): GDELT fetch cycle completed, waiting $FETCH_INTERVAL seconds" >> "$LOG_FILE"
        sleep "$FETCH_INTERVAL"
    done &
    
    # Save PID
    echo $! > "$PID_FILE"
    echo "GDELT fetcher daemon started (PID: $(cat "$PID_FILE"))"
}

# Function to stop the daemon
stop_daemon() {
    if ! is_running; then
        echo "GDELT fetcher daemon is not running"
        return
    fi
    
    echo "Stopping GDELT fetcher daemon..."
    PID=$(cat "$PID_FILE")
    
    # Kill the process group
    kill -TERM -"$PID" 2>/dev/null
    
    # Wait for the process to terminate
    for i in {1..10}; do
        if ! ps -p "$PID" > /dev/null; then
            break
        fi
        sleep 1
    done
    
    # Force kill if still running
    if ps -p "$PID" > /dev/null; then
        echo "Force killing GDELT fetcher daemon..."
        kill -9 -"$PID" 2>/dev/null
    fi
    
    # Remove PID file
    rm -f "$PID_FILE"
    echo "GDELT fetcher daemon stopped"
}

# Function to check the status of the daemon
status_daemon() {
    if is_running; then
        echo "GDELT fetcher daemon is running (PID: $(cat "$PID_FILE"))"
    else
        echo "GDELT fetcher daemon is not running"
    fi
}

# Function to view the daemon log
view_log() {
    if [ -f "$LOG_FILE" ]; then
        tail -n 50 "$LOG_FILE"
    else
        echo "Log file not found"
    fi
}

# Parse command line arguments
case "$1" in
    start)
        start_daemon
        ;;
    stop)
        stop_daemon
        ;;
    restart)
        stop_daemon
        start_daemon
        ;;
    status)
        status_daemon
        ;;
    log)
        view_log
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|log}"
        exit 1
        ;;
esac

exit 0
