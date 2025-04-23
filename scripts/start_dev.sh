#!/bin/bash

# Hydra News Development Startup Script

echo "Starting Hydra News development environment..."

# Create necessary directories
mkdir -p logs

# Compile C libraries
echo "Compiling C components..."
cd c
gcc -c -fPIC src/quantum_zkp.c -o quantum_zkp.o
gcc -shared -o libquantumzkp.so quantum_zkp.o
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$(pwd)
cd ..

# Start Go backend
echo "Starting Go backend services..."
cd go
go build -o ../bin/identity_service src/identity/*.go
go build -o ../bin/consensus_service src/consensus/*.go
cd ..

# Start Identity Service
./bin/identity_service --port 8080 > logs/identity.log 2>&1 &
IDENTITY_PID=$!
echo "Identity Service started (PID: $IDENTITY_PID)"

# Start Consensus Service
./bin/consensus_service --port 8081 > logs/consensus.log 2>&1 &
CONSENSUS_PID=$!
echo "Consensus Service started (PID: $CONSENSUS_PID)"

# Start Python content processor
echo "Starting Python content processor..."
cd python
python -m src.content_processor > ../logs/content_processor.log 2>&1 &
PROCESSOR_PID=$!
echo "Content Processor started (PID: $PROCESSOR_PID)"
cd ..

# Start TypeScript frontend
echo "Starting TypeScript frontend..."
cd typescript
npm start > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "Frontend started (PID: $FRONTEND_PID)"
cd ..

# Save PIDs for cleanup
echo "$IDENTITY_PID $CONSENSUS_PID $PROCESSOR_PID $FRONTEND_PID" > .dev_pids

echo "Development environment started!"
echo "API Endpoints:"
echo "  - Identity Service: http://localhost:8080"
echo "  - Consensus Service: http://localhost:8081"
echo "  - Content Processor: http://localhost:8082"
echo "  - Frontend: http://localhost:3000"
echo ""
echo "To stop all services, run: ./scripts/stop_dev.sh"
