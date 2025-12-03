#!/usr/bin/env python3
"""
Start FastAPI server with MongoDB on port 8001
"""
import os
import uvicorn

# Set environment variables for MongoDB
os.environ['DATABASE_TYPE'] = 'mongodb'
os.environ['DATABASE_URL'] = 'mongodb://localhost:27017'
os.environ['MONGODB_DATABASE'] = 'fastapi_crud_test'

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )
