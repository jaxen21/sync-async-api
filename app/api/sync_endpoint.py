"""Synchronous API endpoint."""
import asyncio
import time
import uuid
from fastapi import APIRouter, Request, HTTPException
from ..core.schemas import SyncRequest, SyncResponse
from ..core.work import do_work
from ..db.connection import get_db
from ..db import repository
from ..config import get_settings


settings = get_settings()
router = APIRouter()

# Semaphore to limit concurrent sync requests
sync_semaphore = asyncio.Semaphore(settings.max_sync_concurrency)


@router.post("/sync", response_model=SyncResponse)
async def sync_endpoint(
    request_data: SyncRequest,
    request: Request
):
    """
    Synchronous request processing.
    
    Executes work immediately and returns result.
    Limited by semaphore to prevent overload.
    """
    # Try to acquire semaphore
    if sync_semaphore.locked() and sync_semaphore._value == 0:
        raise HTTPException(
            status_code=503,
            detail="Server is at maximum capacity. Please try again later."
        )
    
    async with sync_semaphore:
        request_id = str(uuid.uuid4())
        client_ip = request.client.host if request.client else "unknown"
        
        # Store request
        async with get_db() as conn:
            await repository.create_request(
                conn,
                request_id,
                "sync",
                request_data.payload.model_dump(),
                None,
                client_ip
            )
        
        # Update to processing
        start_time = time.time()
        async with get_db() as conn:
            await repository.update_request_status(
                conn,
                request_id,
                "processing",
                started_at=start_time
            )
        
        try:
            # Execute work with timeout
            result = await asyncio.wait_for(
                do_work(request_data.payload),
                timeout=settings.work_timeout_seconds
            )
            
            execution_time_ms = (time.time() - start_time) * 1000
            
            # Update result
            async with get_db() as conn:
                await repository.update_request_result(conn, request_id, result)
                await repository.update_request_status(
                    conn,
                    request_id,
                    "done",
                    completed_at=time.time()
                )
            
            return SyncResponse(
                request_id=request_id,
                status="done",
                result=result,
                error=None,
                execution_time_ms=execution_time_ms
            )
        
        except asyncio.TimeoutError:
            error_msg = f"Work execution timeout after {settings.work_timeout_seconds}s"
            execution_time_ms = settings.work_timeout_seconds * 1000
            
            async with get_db() as conn:
                await repository.update_request_result(conn, request_id, None, error_msg)
                await repository.update_request_status(
                    conn,
                    request_id,
                    "failed",
                    completed_at=time.time()
                )
            
            return SyncResponse(
                request_id=request_id,
                status="failed",
                result=None,
                error=error_msg,
                execution_time_ms=execution_time_ms
            )
        
        except Exception as e:
            error_msg = f"Work execution error: {str(e)}"
            execution_time_ms = (time.time() - start_time) * 1000
            
            async with get_db() as conn:
                await repository.update_request_result(conn, request_id, None, error_msg)
                await repository.update_request_status(
                    conn,
                    request_id,
                    "failed",
                    completed_at=time.time()
                )
            
            return SyncResponse(
                request_id=request_id,
                status="failed",
                result=None,
                error=error_msg,
                execution_time_ms=execution_time_ms
            )
