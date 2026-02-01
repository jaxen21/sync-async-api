"""Query endpoints for observability."""
import json
import time
from fastapi import APIRouter, HTTPException, Query
from ..core.schemas import RequestStatus, RequestListResponse, MetricsResponse, HealthResponse
from ..db.connection import get_db
from ..db import repository
from ..worker.queue_manager import queue_manager
from ..config import get_settings


settings = get_settings()
router = APIRouter()


@router.get("/requests/{request_id}", response_model=RequestStatus)
async def get_request(request_id: str):
    """Get details of a specific request."""
    async with get_db() as conn:
        req = await repository.get_request(conn, request_id)
    
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    
    # Parse JSON fields
    payload = json.loads(req["payload"])
    result = json.loads(req["result"]) if req["result"] else None
    
    # Calculate execution time
    execution_time_ms = None
    if req["started_at"] and req["completed_at"]:
        execution_time_ms = (req["completed_at"] - req["started_at"]) * 1000
    
    return RequestStatus(
        request_id=req["id"],
        mode=req["mode"],
        status=req["status"],
        payload=payload,
        result=result,
        created_at=req["created_at"],
        completed_at=req["completed_at"],
        execution_time_ms=execution_time_ms,
        attempts=req["attempts"],
        last_error=req["last_error"]
    )


@router.get("/requests", response_model=RequestListResponse)
async def list_requests(
    mode: str | None = Query(None, description="Filter by mode (sync/async)"),
    status: str | None = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=100, description="Results per page"),
    offset: int = Query(0, ge=0, description="Pagination offset")
):
    """List all requests with filtering and pagination."""
    async with get_db() as conn:
        requests, total = await repository.list_requests(conn, mode, status, limit, offset)
    
    # Parse JSON fields
    request_list = []
    for req in requests:
        payload = json.loads(req["payload"])
        result = json.loads(req["result"]) if req["result"] else None
        
        execution_time_ms = None
        if req["started_at"] and req["completed_at"]:
            execution_time_ms = (req["completed_at"] - req["started_at"]) * 1000
        
        request_list.append(RequestStatus(
            request_id=req["id"],
            mode=req["mode"],
            status=req["status"],
            payload=payload,
            result=result,
            created_at=req["created_at"],
            completed_at=req["completed_at"],
            execution_time_ms=execution_time_ms,
            attempts=req["attempts"],
            last_error=req["last_error"]
        ))
    
    return RequestListResponse(
        total=total,
        limit=limit,
        offset=offset,
        requests=request_list
    )


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics():
    """Get system metrics."""
    async with get_db() as conn:
        db_metrics = await repository.get_metrics(conn)
    
    queue_metrics = queue_manager.get_metrics()
    
    return MetricsResponse(
        timestamp=time.time(),
        total_requests=db_metrics["total_requests"],
        by_mode=db_metrics["by_mode"],
        by_status=db_metrics["by_status"],
        avg_execution_time_ms=db_metrics["avg_execution_time_ms"],
        queue=queue_metrics,
        workers={
            "total": settings.num_workers,
            "active": settings.num_workers  # Simplified - all workers are always active
        }
    )


@router.get("/healthz", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    try:
        # Check database
        async with get_db() as conn:
            cursor = await conn.execute("SELECT 1")
            await cursor.fetchone()
        db_status = "connected"
    except Exception:
        db_status = "disconnected"
    
    queue_size = queue_manager.get_size()
    
    is_healthy = db_status == "connected"
    
    return HealthResponse(
        status="healthy" if is_healthy else "unhealthy",
        timestamp=time.time(),
        database=db_status,
        workers="running",
        queue_size=queue_size
    )
