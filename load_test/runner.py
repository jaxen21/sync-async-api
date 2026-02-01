"""Load test runner."""
import asyncio
import httpx
import time
import argparse
import statistics
from typing import List


class LoadTestRunner:
    """Load test runner for sync/async APIs."""
    
    def __init__(
        self,
        base_url: str,
        mode: str,
        total_requests: int,
        concurrency: int,
        complexity: int,
        callback_url: str | None = None
    ):
        self.base_url = base_url
        self.mode = mode
        self.total_requests = total_requests
        self.concurrency = concurrency
        self.complexity = complexity
        self.callback_url = callback_url
        
        self.results: List[dict] = []
        self.errors: List[dict] = []
    
    async def send_sync_request(self, client: httpx.AsyncClient, request_num: int):
        """Send a synchronous request."""
        start_time = time.time()
        
        try:
            response = await client.post(
                f"{self.base_url}/sync",
                json={
                    "payload": {
                        "operation": "hash",
                        "complexity": self.complexity
                    }
                },
                timeout=60.0
            )
            
            elapsed = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                self.results.append({
                    "request_num": request_num,
                    "latency_ms": elapsed,
                    "status": "success",
                    "execution_time_ms": data.get("execution_time_ms", 0)
                })
            else:
                self.errors.append({
                    "request_num": request_num,
                    "status_code": response.status_code,
                    "error": response.text
                })
        
        except Exception as e:
            self.errors.append({
                "request_num": request_num,
                "error": str(e)
            })
    
    async def send_async_request(self, client: httpx.AsyncClient, request_num: int):
        """Send an asynchronous request."""
        start_time = time.time()
        
        try:
            response = await client.post(
                f"{self.base_url}/async",
                json={
                    "payload": {
                        "operation": "prime",
                        "complexity": self.complexity
                    },
                    "callback_url": self.callback_url
                },
                timeout=10.0
            )
            
            elapsed = (time.time() - start_time) * 1000
            
            if response.status_code == 202:
                self.results.append({
                    "request_num": request_num,
                    "ack_latency_ms": elapsed,
                    "status": "success"
                })
            else:
                self.errors.append({
                    "request_num": request_num,
                    "status_code": response.status_code,
                    "error": response.text
                })
        
        except Exception as e:
            self.errors.append({
                "request_num": request_num,
                "error": str(e)
            })
    
    async def run(self):
        """Run the load test."""
        print(f"\n{'='*60}")
        print(f"Load Test Configuration")
        print(f"{'='*60}")
        print(f"Mode: {self.mode}")
        print(f"Total Requests: {self.total_requests}")
        print(f"Concurrency: {self.concurrency}")
        print(f"Complexity: {self.complexity}")
        if self.callback_url:
            print(f"Callback URL: {self.callback_url}")
        print(f"{'='*60}\n")
        
        start_time = time.time()
        
        async with httpx.AsyncClient() as client:
            # Create batches of concurrent requests
            for batch_start in range(0, self.total_requests, self.concurrency):
                batch_end = min(batch_start + self.concurrency, self.total_requests)
                batch_size = batch_end - batch_start
                
                print(f"Sending batch {batch_start//self.concurrency + 1}: "
                      f"requests {batch_start+1}-{batch_end}")
                
                tasks = []
                for i in range(batch_start, batch_end):
                    if self.mode == "sync":
                        task = self.send_sync_request(client, i + 1)
                    else:
                        task = self.send_async_request(client, i + 1)
                    tasks.append(task)
                
                await asyncio.gather(*tasks)
        
        total_time = time.time() - start_time
        
        # Print results
        self.print_results(total_time)
    
    def print_results(self, total_time: float):
        """Print test results."""
        print(f"\n{'='*60}")
        print(f"Load Test Results")
        print(f"{'='*60}")
        
        success_count = len(self.results)
        error_count = len(self.errors)
        total = success_count + error_count
        
        print(f"Total Requests: {total}")
        print(f"Successful: {success_count} ({success_count/total*100:.1f}%)")
        print(f"Failed: {error_count} ({error_count/total*100:.1f}%)")
        print(f"Total Time: {total_time:.2f}s")
        print(f"Throughput: {total/total_time:.2f} req/s")
        
        if self.results:
            if self.mode == "sync":
                latencies = [r["latency_ms"] for r in self.results]
                exec_times = [r["execution_time_ms"] for r in self.results]
                
                print(f"\nResponse Time (ms):")
                print(f"  Min: {min(latencies):.2f}")
                print(f"  Max: {max(latencies):.2f}")
                print(f"  Mean: {statistics.mean(latencies):.2f}")
                print(f"  Median: {statistics.median(latencies):.2f}")
                
                if len(latencies) > 1:
                    print(f"  p95: {statistics.quantiles(latencies, n=20)[18]:.2f}")
                    print(f"  p99: {statistics.quantiles(latencies, n=100)[98]:.2f}")
                
                print(f"\nExecution Time (ms):")
                print(f"  Mean: {statistics.mean(exec_times):.2f}")
            
            else:  # async
                ack_latencies = [r["ack_latency_ms"] for r in self.results]
                
                print(f"\nAck Latency (ms):")
                print(f"  Min: {min(ack_latencies):.2f}")
                print(f"  Max: {max(ack_latencies):.2f}")
                print(f"  Mean: {statistics.mean(ack_latencies):.2f}")
                print(f"  Median: {statistics.median(ack_latencies):.2f}")
        
        if self.errors:
            print(f"\nErrors:")
            for error in self.errors[:5]:  # Show first 5 errors
                print(f"  Request {error['request_num']}: {error.get('error', error.get('status_code'))}")
            if len(self.errors) > 5:
                print(f"  ... and {len(self.errors) - 5} more")
        
        print(f"{'='*60}\n")


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Load test runner for sync/async API")
    parser.add_argument("--mode", choices=["sync", "async"], required=True, help="Test mode")
    parser.add_argument("--requests", type=int, default=100, help="Total number of requests")
    parser.add_argument("--concurrency", type=int, default=10, help="Concurrent requests")
    parser.add_argument("--complexity", type=int, default=5, choices=range(1, 11), help="Work complexity (1-10)")
    parser.add_argument("--url", type=str, default="http://localhost:8000", help="API base URL")
    parser.add_argument("--callback-port", type=int, default=9000, help="Callback server port (for async mode)")
    
    args = parser.parse_args()
    
    callback_url = None
    if args.mode == "async":
        callback_url = f"http://localhost:{args.callback_port}/callback"
    
    runner = LoadTestRunner(
        base_url=args.url,
        mode=args.mode,
        total_requests=args.requests,
        concurrency=args.concurrency,
        complexity=args.complexity,
        callback_url=callback_url
    )
    
    await runner.run()


if __name__ == "__main__":
    asyncio.run(main())
