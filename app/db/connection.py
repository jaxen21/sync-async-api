"""Database connection management."""
import aiosqlite
from contextlib import asynccontextmanager
from pathlib import Path
from ..config import get_settings


settings = get_settings()


@asynccontextmanager
async def get_db():
    """Get database connection."""
    db_path = Path(settings.database_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    async with aiosqlite.connect(db_path) as conn:
        conn.row_factory = aiosqlite.Row
        yield conn


async def init_database():
    """Initialize database with schema."""
    schema_path = Path(__file__).parent / "schema.sql"
    
    async with get_db() as conn:
        with open(schema_path) as f:
            await conn.executescript(f.read())
        await conn.commit()
