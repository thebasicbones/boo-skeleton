#!/bin/bash
# Start FastAPI server with MongoDB on port 8001

# Copy MongoDB env file
cp .env.mongodb .env

# Start the server
./venv/bin/python -c "
import uvicorn
import os

# Set environment variables
os.environ['DATABASE_TYPE'] = 'mongodb'
os.environ['DATABASE_URL'] = 'mongodb://localhost:27017'
os.environ['MONGODB_DATABASE'] = 'fastapi_crud_test'

# Run the server
uvicorn.run(
    'main:app',
    host='0.0.0.0',
    port=8001,
    reload=False,
    log_level='info'
)
"
