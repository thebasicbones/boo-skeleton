"""Database initialization script"""
import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from app.database_factory import init_database

# Load environment variables
load_dotenv()


async def main():
    """Initialize the database"""
    db_type = os.getenv("DATABASE_TYPE", "sqlite")
    print(f"Initializing {db_type} database...")
    
    try:
        await init_database()
        print("Database initialized successfully!")
    except Exception as e:
        print(f"Error initializing database: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
