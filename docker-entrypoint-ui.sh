#!/bin/bash
# Entrypoint script for UI container
# Waits for API to be ready, then starts Streamlit
set -e

echo "🎨 Starting UI container..."

# Change to app directory
cd /app

# Wait for API to be ready
echo "⏳ Waiting for API to be ready..."
until curl -s http://api:8000/health > /dev/null 2>&1; do
    echo "   ⏳ API not ready yet, waiting..."
    sleep 2
done

echo "✅ API is ready!"

# Start Streamlit
echo "🚀 Starting Streamlit UI..."
exec streamlit run ui/app.py --server.port=8501 --server.address=0.0.0.0
