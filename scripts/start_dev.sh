#!/bin/bash

# Hydra News Development Startup Script

echo "Starting Hydra News development environment..."

# Create necessary directories
mkdir -p logs
mkdir -p bin

# Compile C libraries
echo "Compiling C components..."
cd c
gcc -c -fPIC src/quantum_zkp.c -o quantum_zkp.o
gcc -shared -o libquantumzkp.so quantum_zkp.o
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$(pwd)
cd ..

# Build Go backend
echo "Building Go components..."
cd go
go mod init hydranews 2>/dev/null || true
go get github.com/gorilla/mux
go get github.com/rs/cors
go build -o ../bin/hydra_news_api src/main.go
cd ..

# Install Python dependencies
echo "Installing Python dependencies..."
cd python
pip install -r requirements.txt
cd ..

# Install TypeScript dependencies
echo "Installing TypeScript dependencies..."
cd typescript
npm install --silent || true
cd ..

# Start Python content processor service
echo "Starting Python content processor service..."
cd python
python src/content_processor_service.py --port 5000 > ../logs/content_processor.log 2>&1 &
PROCESSOR_PID=$!
echo "Content Processor Service started (PID: $PROCESSOR_PID)"
cd ..

# Wait for Python service to start
sleep 2

# Start Go API service
echo "Starting Go API service..."
./bin/hydra_news_api --port 8080 > logs/api.log 2>&1 &
API_PID=$!
echo "API Service started (PID: $API_PID)"

# Start TypeScript frontend
echo "Starting TypeScript frontend..."
cd typescript
npm start > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "Frontend started (PID: $FRONTEND_PID)"
cd ..

# Save PIDs for cleanup
echo "$PROCESSOR_PID $API_PID $FRONTEND_PID" > .dev_pids

echo "Development environment started!"
echo "API Endpoints:"
echo "  - Main API Service: http://localhost:8080"
echo "  - Content Processor Service: http://localhost:5000"
echo "  - Frontend: http://localhost:3000"
echo ""
echo "To stop all services, run: ./scripts/stop_dev.sh"
