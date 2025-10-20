#!/bin/bash
"""
Entrypoint script for API container
Initializes database if needed, then starts the API
"""
set -e

echo "🔧 Starting API container..."

# Change to app directory
cd /app

# Initialize database if needed
echo "📊 Checking database initialization..."
python scripts/init_docker.py

# Start the API
echo "🚀 Starting FastAPI server..."
exec uvicorn api.main:app --host 0.0.0.0 --port 8000
