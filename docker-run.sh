#!/bin/bash

# Docker script to build and run the SecureChat application
# This script makes it easy to run the application on any system

# Create necessary directories if they don't exist
mkdir -p instance logs

# Build the Docker image
echo "Building Docker image..."
docker build -t securechat .

# Run the Docker container
echo "Starting SecureChat container..."
docker run -p 5000:5000 \
  -v "$(pwd)/instance:/app/instance" \
  -v "$(pwd)/logs:/app/logs" \
  securechat

# Note: To run in detached mode, add -d flag:
# docker run -d -p 5000:5000 -v "$(pwd)/instance:/app/instance" -v "$(pwd)/logs:/app/logs" securechat
