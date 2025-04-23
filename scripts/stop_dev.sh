#!/bin/bash

# Hydra News Development Shutdown Script

echo "Stopping Hydra News development environment..."

# Check if PID file exists
if [ -f .dev_pids ]; then
  # Read PIDs from file
  PIDS=$(cat .dev_pids)
  
  # Kill each process
  for PID in $PIDS; do
    if ps -p $PID > /dev/null; then
      echo "Stopping process with PID: $PID"
      kill $PID
    else
      echo "Process with PID $PID is no longer running"
    fi
  done
  
  # Remove PID file
  rm .dev_pids
  echo "All services stopped."
else
  echo "No PID file found. Services may not be running."
  
  # Try to find and kill processes by name as a fallback
  echo "Attempting to find and stop services by name..."
  
  # Kill identity service
  pkill -f "identity_service"
  
  # Kill consensus service
  pkill -f "consensus_service"
  
  # Kill Python content processor
  pkill -f "src.content_processor"
  
  # Kill TypeScript frontend
  pkill -f "npm start"
  
  echo "Done."
fi
