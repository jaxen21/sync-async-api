"""Main FastAPI application."""
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .db.connection import init_database
from .worker.processor import worker_loop
from .utils.rate_limiter import rate_limiter
from .api import sync_endpoint, async_endpoint, queries


settings = get_settings()

# Worker tasks
worker_tasks = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    print("Initializing database...")
    await init_database()
    print("Database initialized")
    
    # Start workers
    print(f"Starting {settings.num_workers} workers...")
    for i in range(settings.num_workers):
        task = asyncio.create_task(worker_loop(i))
        worker_tasks.append(task)
    print(f"{settings.num_workers} workers started")
    
    yield
    
    # Shutdown
    print("Shutting down workers...")
    for task in worker_tasks:
        task.cancel()
    await asyncio.gather(*worker_tasks, return_exceptions=True)
    print("Workers shut down")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="Demonstration of sync vs async API patterns",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Rate limiting middleware
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Rate limiting middleware."""
    client_ip = request.client.host if request.client else "unknown"
    
    # Skip rate limiting for health check
    if request.url.path == "/healthz":
        return await call_next(request)
    
    is_allowed, retry_after = rate_limiter.check_rate_limit(client_ip)
    
    if not is_allowed:
        return JSONResponse(
            status_code=429,
            content={
                "detail": f"Rate limit exceeded. Try again in {retry_after} seconds.",
                "retry_after": retry_after
            },
            headers={
                "Retry-After": str(retry_after),
                "X-RateLimit-Limit": str(settings.rate_limit_requests),
                "X-RateLimit-Remaining": "0",
            }
        )
    
    response = await call_next(request)
    return response


# Include routers
app.include_router(sync_endpoint.router, tags=["Sync API"])
app.include_router(async_endpoint.router, tags=["Async API"])
app.include_router(queries.router, tags=["Queries"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Sync vs Async API Demo",
        "docs": "/docs",
        "health": "/healthz",
        "metrics": "/metrics"
    }
