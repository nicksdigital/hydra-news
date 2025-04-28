#!/bin/bash
# Script to run the dashboard and process chunks simultaneously

# Activate the virtual environment
source venv/bin/activate

# Start the dashboard in the background
echo "Starting the dashboard..."
python -m python.src.gdelt.run_dashboard --port 5001 --no-browser &
DASHBOARD_PID=$!

# Wait for the dashboard to start
echo "Waiting for the dashboard to start..."
sleep 5

# Open the dashboard in the browser
echo "Opening the dashboard in the browser..."
python -c "import webbrowser; webbrowser.open('http://127.0.0.1:5001')"

# Start processing chunks with a delay
echo "Starting to process chunks..."
python process_chunks_sequentially.py --delay 20 --limit 10

# Wait for the user to press Ctrl+C
echo "Press Ctrl+C to stop the dashboard and exit"
wait $DASHBOARD_PID
