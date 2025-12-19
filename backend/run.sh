#!/bin/bash
# Startup script for backend development

echo "Starting HealthPulse Registry Backend..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "Creating .env from env.example..."
    cp env.example .env
    echo "Please edit .env with your database credentials"
fi

# Initialize database if needed
echo "Initializing database..."
python init_db.py

# Start the server
echo "Starting FastAPI server..."
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

