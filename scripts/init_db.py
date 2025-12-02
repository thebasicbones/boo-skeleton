"""Database initialization script"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import init_db, drop_db


async def main():
    """Initialize the database"""
    print("Initializing database...")
    
    # Optionally drop existing tables (uncomment if needed)
    # print("Dropping existing tables...")
    # await drop_db()
    
    print("Creating tables...")
    await init_db()
    
    print("Database initialized successfully!")


if __name__ == "__main__":
    asyncio.run(main())
