"""Database repository - raw SQL operations."""
import json
import time
from typing import Any
import aiosqlite


async def create_request(
    conn: aiosqlite.Connection,
    request_id: str,
    mode: str,
    payload: dict,
    callback_url: str | None,
    client_ip: str
) -> None:
    """Create a new request record."""
    await conn.execute(
        """
        INSERT INTO requests 
        (id, mode, payload, status, callback_url, created_at, client_ip)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            request_id,
            mode,
            json.dumps(payload),
            "pending",
            callback_url,
            time.time(),
            client_ip
        )
    )
    await conn.commit()


async def get_request(conn: aiosqlite.Connection, request_id: str) -> dict | None:
    """Get a single request by ID."""
    cursor = await conn.execute(
        "SELECT * FROM requests WHERE id = ?",
        (request_id,)
    )
    row = await cursor.fetchone()
    
    if not row:
        return None
    
    return dict(row)


async def list_requests(
    conn: aiosqlite.Connection,
    mode: str | None = None,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0
) -> tuple[list[dict], int]:
    """List requests with filtering and pagination."""
    # Build query
    where_clauses = []
    params = []
    
    if mode:
        where_clauses.append("mode = ?")
        params.append(mode)
    
    if status:
        where_clauses.append("status = ?")
        params.append(status)
    
    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
    
    # Get total count
    count_cursor = await conn.execute(
        f"SELECT COUNT(*) FROM requests {where_sql}",
        params
    )
    total = (await count_cursor.fetchone())[0]
    
    # Get paginated results
    cursor = await conn.execute(
        f"""
        SELECT * FROM requests {where_sql}
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
        """,
        params + [limit, offset]
    )
    rows = await cursor.fetchall()
    
    return [dict(row) for row in rows], total


async def update_request_status(
    conn: aiosqlite.Connection,
    request_id: str,
    status: str,
    started_at: float | None = None,
    completed_at: float | None = None
) -> None:
    """Update request status."""
    updates = ["status = ?"]
    params = [status]
    
    if started_at is not None:
        updates.append("started_at = ?")
        params.append(started_at)
    
    if completed_at is not None:
        updates.append("completed_at = ?")
        params.append(completed_at)
    
    params.append(request_id)
    
    await conn.execute(
        f"UPDATE requests SET {', '.join(updates)} WHERE id = ?",
        params
    )
    await conn.commit()


async def update_request_result(
    conn: aiosqlite.Connection,
    request_id: str,
    result: dict | None,
    error: str | None = None
) -> None:
    """Update request result."""
    await conn.execute(
        "UPDATE requests SET result = ?, last_error = ? WHERE id = ?",
        (json.dumps(result) if result else None, error, request_id)
    )
    await conn.commit()


async def increment_callback_attempts(
    conn: aiosqlite.Connection,
    request_id: str,
    error: str | None = None
) -> None:
    """Increment callback attempt counter."""
    await conn.execute(
        """
        UPDATE requests 
        SET attempts = attempts + 1, last_error = ?
        WHERE id = ?
        """,
        (error, request_id)
    )
    await conn.commit()


async def get_metrics(conn: aiosqlite.Connection) -> dict[str, Any]:
    """Get system metrics."""
    # Total requests
    cursor = await conn.execute("SELECT COUNT(*) FROM requests")
    total = (await cursor.fetchone())[0]
    
    # By mode
    cursor = await conn.execute(
        "SELECT mode, COUNT(*) FROM requests GROUP BY mode"
    )
    by_mode = {row[0]: row[1] for row in await cursor.fetchall()}
    
    # By status
    cursor = await conn.execute(
        "SELECT status, COUNT(*) FROM requests GROUP BY status"
    )
    by_status = {row[0]: row[1] for row in await cursor.fetchall()}
    
    # Average execution time
    cursor = await conn.execute(
        """
        SELECT mode, AVG((completed_at - started_at) * 1000) as avg_ms
        FROM requests
        WHERE completed_at IS NOT NULL AND started_at IS NOT NULL
        GROUP BY mode
        """
    )
    avg_time = {row[0]: row[1] or 0 for row in await cursor.fetchall()}
    
    return {
        "total_requests": total,
        "by_mode": by_mode,
        "by_status": by_status,
        "avg_execution_time_ms": avg_time
    }
