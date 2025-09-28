#!/bin/bash

# Function to clean up background processes
cleanup() {
    echo "Stopping processes..."
    kill $BACKEND_PID
}

# Trap Ctrl+C to call cleanup
trap cleanup INT

# Start backend
echo "Starting backend..."
source venv_local/bin/activate
python3 app_cors_livre.py --port 5004 &
BACKEND_PID=$!
echo "Backend started with PID $BACKEND_PID"

# Wait for backend to initialize (adjust sleep as needed)
sleep 5

# Start frontend on a free port
echo "Starting frontend on a free port..."
cd "frontend"
PORT=3001 npm start --reset-cache

# Call cleanup when frontend exits
cleanup
