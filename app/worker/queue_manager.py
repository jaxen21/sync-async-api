"""Queue manager for async job processing."""
import asyncio
from typing import Any
from ..config import get_settings


settings = get_settings()


class QueueManager:
    """Manages the async job queue."""
    
    def __init__(self):
        self.queue: asyncio.Queue = asyncio.Queue(maxsize=settings.max_queue_size)
        self.total_enqueued = 0
        self.total_processed = 0
    
    async def enqueue(self, job: dict[str, Any]) -> bool:
        """
        Enqueue a job.
        
        Returns:
            True if enqueued, False if queue is full
        """
        try:
            self.queue.put_nowait(job)
            self.total_enqueued += 1
            return True
        except asyncio.QueueFull:
            return False
    
    async def dequeue(self) -> dict[str, Any]:
        """Dequeue a job (blocks if empty)."""
        job = await self.queue.get()
        return job
    
    def task_done(self):
        """Mark task as done."""
        self.queue.task_done()
        self.total_processed += 1
    
    def get_size(self) -> int:
        """Get current queue size."""
        return self.queue.qsize()
    
    def get_metrics(self) -> dict[str, int]:
        """Get queue metrics."""
        return {
            "current_size": self.get_size(),
            "max_size": settings.max_queue_size,
            "total_enqueued": self.total_enqueued,
            "total_processed": self.total_processed
        }


# Global queue instance
queue_manager = QueueManager()
