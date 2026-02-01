"""Callback delivery with retry logic."""
import asyncio
import httpx
import json
from ..config import get_settings


settings = get_settings()


async def deliver_callback(
    callback_url: str,
    payload: dict,
    request_id: str
) -> tuple[bool, str | None]:
    """
    Deliver callback with exponential backoff retry.
    
    Returns:
        (success, error_message)
    """
    max_retries = settings.max_callback_retries
    timeout = settings.callback_timeout_seconds
    backoff_base = settings.retry_backoff_base
    
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    callback_url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code < 400:
                    return True, None
                else:
                    error = f"HTTP {response.status_code}: {response.text[:100]}"
        
        except httpx.TimeoutException:
            error = f"Timeout after {timeout}s"
        except httpx.RequestError as e:
            error = f"Request error: {str(e)[:100]}"
        except Exception as e:
            error = f"Unexpected error: {str(e)[:100]}"
        
        # Retry with exponential backoff
        if attempt < max_retries - 1:
            wait_time = backoff_base ** attempt
            await asyncio.sleep(wait_time)
    
    return False, f"Failed after {max_retries} attempts. Last error: {error}"
