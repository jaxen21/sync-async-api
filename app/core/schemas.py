"""Pydantic models for request/response validation."""
from pydantic import BaseModel, Field, HttpUrl
from typing import Literal, Any


class WorkPayload(BaseModel):
    """Input to the work engine."""
    operation: Literal["hash", "prime", "matrix", "transform"]
    complexity: int = Field(ge=1, le=10, description="Work complexity (1=fast, 10=slow)")
    data: dict[str, Any] = Field(default_factory=dict, description="Operation-specific data")


class SyncRequest(BaseModel):
    """Synchronous API request."""
    payload: WorkPayload


class AsyncRequest(BaseModel):
    """Asynchronous API request."""
    payload: WorkPayload
    callback_url: HttpUrl


class SyncResponse(BaseModel):
    """Synchronous API response."""
    request_id: str
    status: Literal["done", "failed"]
    result: dict[str, Any] | None
    error: str | None
    execution_time_ms: float


class AsyncResponse(BaseModel):
    """Asynchronous API acknowledgment response."""
    request_id: str
    status: Literal["pending"]
    message: str


class RequestStatus(BaseModel):
    """Request status response."""
    request_id: str
    mode: Literal["sync", "async"]
    status: Literal["pending", "processing", "done", "failed"]
    payload: dict[str, Any]
    result: dict[str, Any] | None
    created_at: float
    completed_at: float | None
    execution_time_ms: float | None
    attempts: int
    last_error: str | None


class RequestListResponse(BaseModel):
    """List of requests response."""
    total: int
    limit: int
    offset: int
    requests: list[RequestStatus]


class MetricsResponse(BaseModel):
    """System metrics response."""
    timestamp: float
    total_requests: int
    by_mode: dict[str, int]
    by_status: dict[str, int]
    avg_execution_time_ms: dict[str, float]
    queue: dict[str, int]
    workers: dict[str, int]


class HealthResponse(BaseModel):
    """Health check response."""
    status: Literal["healthy", "unhealthy"]
    timestamp: float
    database: str
    workers: str
    queue_size: int
