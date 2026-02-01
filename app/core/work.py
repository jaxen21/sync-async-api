"""Work engine - core business logic."""
import asyncio
import hashlib
import json
from typing import Any
from .schemas import WorkPayload


async def do_work(payload: WorkPayload) -> dict[str, Any]:
    """
    Execute work based on payload.
    
    Args:
        payload: Work specification
        
    Returns:
        Result dictionary
        
    Raises:
        TimeoutError: If work exceeds timeout
        ValueError: If operation is invalid
    """
    operation = payload.operation
    complexity = payload.complexity
    data = payload.data
    
    # Complexity determines iterations/delay
    iterations = complexity * 200
    
    if operation == "hash":
        return await _hash_operation(data.get("input", "default"), iterations)
    elif operation == "prime":
        return await _prime_operation(data.get("n", 100), complexity)
    elif operation == "matrix":
        return await _matrix_operation(data.get("size", 10 * complexity), complexity)
    elif operation == "transform":
        return await _transform_operation(data.get("items", list(range(10))), iterations)
    else:
        raise ValueError(f"Unknown operation: {operation}")


async def _hash_operation(input_str: str, iterations: int) -> dict[str, Any]:
    """Iterative SHA256 hashing."""
    result = input_str.encode()
    
    for _ in range(iterations):
        result = hashlib.sha256(result).digest()
        # Yield control periodically
        if _ % 100 == 0:
            await asyncio.sleep(0)
    
    return {
        "output": result.hex(),
        "iterations": iterations,
        "operation": "hash"
    }


async def _prime_operation(n: int, complexity: int) -> dict[str, Any]:
    """Find the Nth prime number."""
    def is_prime(num: int) -> bool:
        if num < 2:
            return False
        for i in range(2, int(num ** 0.5) + 1):
            if num % i == 0:
                return False
        return True
    
    count = 0
    num = 2
    prime = 2
    
    # Add some delay based on complexity
    max_checks = n * complexity
    checks = 0
    
    while count < n and checks < max_checks:
        if is_prime(num):
            prime = num
            count += 1
        num += 1
        checks += 1
        
        # Yield control periodically
        if checks % 100 == 0:
            await asyncio.sleep(0)
    
    return {
        "prime": prime,
        "position": count,
        "operation": "prime"
    }


async def _matrix_operation(size: int, complexity: int) -> dict[str, Any]:
    """Simple matrix multiplication simulation."""
    # Create simple matrices
    matrix_a = [[i + j for j in range(min(size, 50))] for i in range(min(size, 50))]
    matrix_b = [[i * j for j in range(min(size, 50))] for i in range(min(size, 50))]
    
    # Simulate work with iterations
    result_sum = 0
    iterations = complexity * 100
    
    for _ in range(iterations):
        for i in range(len(matrix_a)):
            for j in range(len(matrix_b[0])):
                result_sum += matrix_a[i][j] * matrix_b[j][i % len(matrix_b)]
        
        # Yield control periodically
        if _ % 10 == 0:
            await asyncio.sleep(0)
    
    return {
        "result_sum": result_sum,
        "size": size,
        "iterations": iterations,
        "operation": "matrix"
    }


async def _transform_operation(items: list, iterations: int) -> dict[str, Any]:
    """JSON data transformation."""
    result = items.copy()
    
    for _ in range(iterations):
        # Simple transformation: square numbers if numeric
        result = [
            x ** 2 if isinstance(x, (int, float)) else str(x).upper()
            for x in result
        ]
        
        # Yield control periodically
        if _ % 100 == 0:
            await asyncio.sleep(0)
    
    return {
        "transformed": result[:10],  # Limit output size
        "count": len(result),
        "iterations": iterations,
        "operation": "transform"
    }
