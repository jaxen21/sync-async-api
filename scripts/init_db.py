"""Initialize database."""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.connection import init_database


async def main():
    """Initialize the database."""
    print("Initializing database...")
    await init_database()
    print("Database initialized successfully!")


if __name__ == "__main__":
    asyncio.run(main())
