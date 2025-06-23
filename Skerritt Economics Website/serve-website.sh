#!/bin/bash

# Start a local development server for Skerritt Economics Website
# This provides a better development experience with live reload capability

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Function to check if a port is available
is_port_available() {
    ! lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null 2>&1
}

# Find an available port starting from 8080
find_available_port() {
    local port=8080
    while ! is_port_available $port; do
        echo "Port $port is in use, trying next..." >&2
        ((port++))
    done
    echo $port
}

# Find available port
PORT=$(find_available_port)

echo "Starting Skerritt Economics Website development server..."
echo "Server will be available at: http://localhost:$PORT"
echo "Press Ctrl+C to stop the server"
echo ""

# Check if Python 3 is available
if command -v python3 &> /dev/null; then
    echo "Starting Python HTTP server on port $PORT..."
    echo "Opening browser..."
    
    # Open browser automatically
    if [[ "$OSTYPE" == "darwin"* ]]; then
        open "http://localhost:$PORT"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        xdg-open "http://localhost:$PORT"
    elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
        start "http://localhost:$PORT"
    fi
    
    cd "$SCRIPT_DIR"
    python3 -m http.server $PORT
elif command -v python &> /dev/null; then
    # Try Python 2 as fallback
    echo "Starting Python SimpleHTTPServer on port $PORT..."
    
    # Open browser automatically
    if [[ "$OSTYPE" == "darwin"* ]]; then
        open "http://localhost:$PORT"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        xdg-open "http://localhost:$PORT"
    elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
        start "http://localhost:$PORT"
    fi
    
    cd "$SCRIPT_DIR"
    python -m SimpleHTTPServer $PORT
else
    echo "Error: Python is not installed. Please install Python to use this server."
    exit 1
fi