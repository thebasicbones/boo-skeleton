#!/bin/bash
# Startup script for FastAPI CRUD Backend

echo "Starting FastAPI CRUD Backend..."
echo "Server will be available at http://localhost:8000"
echo "API documentation at http://localhost:8000/docs"
echo ""

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run the application
python main.py
