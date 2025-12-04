#!/usr/bin/env python3
"""
Main entry point for the FastAPI application.

This wrapper allows running the application from the project root
while the actual source code lives in the src/ directory.
"""

import sys
from pathlib import Path

# Add src directory to Python path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

# Import and run the application
from main import app, main as run_app

if __name__ == "__main__":
    run_app()
