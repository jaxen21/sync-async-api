"""Asynchronous API endpoint."""
import uuid
from fastapi import APIRouter, Request, HTTPException
from ..core.schemas import AsyncRequest, AsyncResponse
from ..db.connection import get_db
from ..db import repository
from ..worker.queue_manager import queue_manager
from ..utils.url_validator import validate_callback_url


router = APIRouter()


@router.post("/async", response_model=AsyncResponse, status_code=202)
async def async_endpoint(
    request_data: AsyncRequest,
    request: Request
):
    """
    Asynchronous request processing.
    
    Accepts request, enqueues for background processing,
    and returns immediate acknowledgment.
    """
    # Validate callback URL
    is_valid, error = validate_callback_url(str(request_data.callback_url))
    if not is_valid:
        raise HTTPException(status_code=400, detail=error)
    
    request_id = str(uuid.uuid4())
    client_ip = request.client.host if request.client else "unknown"
    
    # Store request
    async with get_db() as conn:
        await repository.create_request(
            conn,
            request_id,
            "async",
            request_data.payload.model_dump(),
            str(request_data.callback_url),
            client_ip
        )
    
    # Enqueue job
    job = {
        "request_id": request_id,
        "payload": request_data.payload.model_dump(),
        "callback_url": str(request_data.callback_url)
    }
    
    enqueued = await queue_manager.enqueue(job)
    
    if not enqueued:
        # Queue is full
        raise HTTPException(
            status_code=429,
            detail="Queue is full. Please try again later."
        )
    
    return AsyncResponse(
        request_id=request_id,
        status="pending",
        message="Request accepted and queued for processing"
    )
