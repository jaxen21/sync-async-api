"""Worker processor for async jobs."""
import asyncio
import time
import json
from ..core.work import do_work
from ..core.schemas import WorkPayload
from ..db.connection import get_db
from ..db import repository
from .callback import deliver_callback
from .queue_manager import queue_manager
from ..config import get_settings


settings = get_settings()


async def worker_loop(worker_id: int):
    """
    Worker loop that processes jobs from the queue.
    
    Args:
        worker_id: Unique worker identifier
    """
    print(f"Worker {worker_id} started")
    
    while True:
        try:
            # Get job from queue
            job = await queue_manager.dequeue()
            
            request_id = job["request_id"]
            payload_dict = job["payload"]
            callback_url = job["callback_url"]
            
            print(f"Worker {worker_id} processing request {request_id}")
            
            # Update status to processing
            async with get_db() as conn:
                await repository.update_request_status(
                    conn,
                    request_id,
                    "processing",
                    started_at=time.time()
                )
            
            try:
                # Execute work
                payload = WorkPayload(**payload_dict)
                
                # Add timeout
                result = await asyncio.wait_for(
                    do_work(payload),
                    timeout=settings.work_timeout_seconds
                )
                
                # Calculate execution time
                async with get_db() as conn:
                    req = await repository.get_request(conn, request_id)
                    execution_time_ms = (time.time() - req["started_at"]) * 1000
                
                # Update result
                async with get_db() as conn:
                    await repository.update_request_result(conn, request_id, result)
                    await repository.update_request_status(
                        conn,
                        request_id,
                        "done",
                        completed_at=time.time()
                    )
                
                # Deliver callback
                callback_payload = {
                    "request_id": request_id,
                    "status": "done",
                    "result": result,
                    "error": None,
                    "execution_time_ms": execution_time_ms,
                    "completed_at": time.time()
                }
                
                success, error = await deliver_callback(
                    callback_url,
                    callback_payload,
                    request_id
                )
                
                if not success:
                    async with get_db() as conn:
                        await repository.increment_callback_attempts(
                            conn,
                            request_id,
                            error
                        )
                    print(f"Callback failed for {request_id}: {error}")
            
            except asyncio.TimeoutError:
                error_msg = f"Work execution timeout after {settings.work_timeout_seconds}s"
                
                async with get_db() as conn:
                    await repository.update_request_result(conn, request_id, None, error_msg)
                    await repository.update_request_status(
                        conn,
                        request_id,
                        "failed",
                        completed_at=time.time()
                    )
                
                # Deliver failure callback
                callback_payload = {
                    "request_id": request_id,
                    "status": "failed",
                    "result": None,
                    "error": error_msg,
                    "execution_time_ms": settings.work_timeout_seconds * 1000,
                    "completed_at": time.time()
                }
                
                await deliver_callback(callback_url, callback_payload, request_id)
            
            except Exception as e:
                error_msg = f"Work execution error: {str(e)}"
                
                async with get_db() as conn:
                    await repository.update_request_result(conn, request_id, None, error_msg)
                    await repository.update_request_status(
                        conn,
                        request_id,
                        "failed",
                        completed_at=time.time()
                    )
                
                # Deliver failure callback
                callback_payload = {
                    "request_id": request_id,
                    "status": "failed",
                    "result": None,
                    "error": error_msg,
                    "execution_time_ms": 0,
                    "completed_at": time.time()
                }
                
                await deliver_callback(callback_url, callback_payload, request_id)
            
            finally:
                queue_manager.task_done()
        
        except Exception as e:
            print(f"Worker {worker_id} error: {e}")
            await asyncio.sleep(1)
