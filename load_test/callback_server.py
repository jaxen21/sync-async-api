"""Simple callback server for testing."""
import time
from fastapi import FastAPI, Request
import uvicorn
import argparse


app = FastAPI(title="Callback Server")

# Store received callbacks
callbacks_received = []


@app.post("/callback")
async def receive_callback(request: Request):
    """Receive callback from async API."""
    data = await request.json()
    
    callback_info = {
        "received_at": time.time(),
        "data": data
    }
    callbacks_received.append(callback_info)
    
    request_id = data.get("request_id", "unknown")
    status = data.get("status", "unknown")
    
    print(f"✓ Callback received for {request_id}: {status}")
    
    if data.get("result"):
        print(f"  Result: {str(data['result'])[:100]}")
    if data.get("error"):
        print(f"  Error: {data['error']}")
    
    return {"status": "received"}


@app.get("/stats")
async def get_stats():
    """Get callback statistics."""
    return {
        "total_received": len(callbacks_received),
        "callbacks": callbacks_received
    }


@app.get("/healthz")
async def health():
    """Health check."""
    return {"status": "healthy"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Callback server for async API testing")
    parser.add_argument("--port", type=int, default=9000, help="Port to listen on")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind to")
    
    args = parser.parse_args()
    
    print(f"Starting callback server on {args.host}:{args.port}")
    print(f"Callback URL: http://localhost:{args.port}/callback")
    
    uvicorn.run(app, host=args.host, port=args.port)
