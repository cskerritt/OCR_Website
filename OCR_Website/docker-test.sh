#!/bin/bash

# This script tests the Docker setup locally before deploying to Lightsail

# Generate a random secret key for testing
export SECRET_KEY=$(openssl rand -hex 16)
echo "Generated random SECRET_KEY for testing: $SECRET_KEY"

# Create required directories if they don't exist
mkdir -p uploads ocr_cache logs/caddy

# Build and start the Docker containers
echo "Building and starting Docker containers..."
docker-compose up --build -d

# Check if containers are running
echo "Checking container status..."
docker-compose ps

# Wait for the application to start
echo "Waiting for the application to start (30 seconds)..."
sleep 30

# Test the application
echo "Testing the application..."
curl -s http://localhost:80 > /dev/null
if [ $? -eq 0 ]; then
    echo "✅ Application is running successfully!"
else
    echo "❌ Application failed to start or is not responding."
    echo "Checking logs..."
    docker-compose logs
fi

echo ""
echo "To stop the containers, run: docker-compose down"
echo "To view logs, run: docker-compose logs"
echo "To access the application, open: http://localhost"
