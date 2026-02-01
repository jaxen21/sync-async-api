# Sync vs Async API Demo

A demonstration comparing synchronous and asynchronous API patterns under high request load using Python and FastAPI.

---

## 🎯 Overview

This project demonstrates the behavioral and performance differences between:

- **Synchronous API** - Processes requests immediately, returns results directly
- **Asynchronous API** - Acknowledges quickly, processes in background, delivers results via callback

Both APIs use the same work engine, making it a fair comparison of the architectural patterns.

---

## 🚀 Quick Start

### 1. Setup

```bash
./setup.sh
```

This will create a virtual environment, install dependencies, and initialize the database.

### 2. Run the Server

```bash
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

**API Documentation:** http://localhost:8000/docs (interactive Swagger UI)

### 3. Test the APIs

**Synchronous Request:**
```bash
curl -X POST http://localhost:8000/sync \
  -H "Content-Type: application/json" \
  -d '{
    "payload": {
      "operation": "hash",
      "complexity": 5
    }
  }'
```

**Asynchronous Request:**

First, start the callback server in a new terminal:
```bash
source venv/bin/activate
python -m load_test.callback_server --port 9000
```

Then send the request:
```bash
curl -X POST http://localhost:8000/async \
  -H "Content-Type: application/json" \
  -d '{
    "payload": {
      "operation": "prime",
      "complexity": 7
    },
    "callback_url": "http://localhost:9000/callback"
  }'
```

---

## 📊 Load Testing

### Sync API Load Test

```bash
python -m load_test.runner \
  --mode sync \
  --requests 50 \
  --concurrency 20 \
  --complexity 5
```

**Expected Results:**
- Response time increases under load (500ms → 5000ms+)
- Limited throughput (~10 req/sec)
- All results returned immediately

### Async API Load Test

```bash
# Ensure callback server is running first
python -m load_test.runner \
  --mode async \
  --requests 50 \
  --concurrency 30 \
  --complexity 5 \
  --callback-port 9000
```

**Expected Results:**
- Fast acknowledgments (<50ms, consistent)
- High throughput (~50+ req/sec for acks)
- Results delivered via callbacks

---

## 🏗️ Architecture

```
Client
  ↓
FastAPI Application
  ├── POST /sync → Semaphore (10) → Work Engine → Response
  └── POST /async → Queue (100) → Workers (5) → Callback
                         ↓
                    SQLite Database
```

**Key Components:**
- **Sync Endpoint:** Semaphore-limited (max 10 concurrent), immediate processing
- **Async Endpoint:** Queue-based (max 100 queued), background workers
- **Work Engine:** 4 operations (hash, prime, matrix, transform) with complexity scaling
- **Database:** SQLite with raw SQL for request tracking
- **Workers:** 5 background workers processing async jobs
- **Callback:** HTTP POST with exponential backoff retry

---

## 📖 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/sync` | Synchronous request processing |
| POST | `/async` | Asynchronous request processing |
| GET | `/requests` | List all requests (with filters) |
| GET | `/requests/{id}` | Get request details |
| GET | `/metrics` | System metrics |
| GET | `/healthz` | Health check |

---

## 🎨 Work Operations

| Operation | Description | Complexity |
|-----------|-------------|------------|
| `hash` | Iterative SHA256 hashing | 1-10 |
| `prime` | Find Nth prime number | 1-10 |
| `matrix` | Matrix multiplication | 1-10 |
| `transform` | JSON data transformation | 1-10 |

**Complexity:** 1 (fast, ~100ms) to 10 (slow, ~5s)

---

## 📊 Performance Comparison

### Under Load (50 requests, complexity 5)

| Metric | Sync API | Async API |
|--------|----------|-----------|
| Ack/Response Time | 500-5000ms (increases) | <50ms (consistent) |
| Throughput | ~10 req/sec | ~50 req/sec |
| Result Delivery | Immediate | Via callback |
| Backpressure | 503 errors | 429 errors |
| Use Case | Low volume | High volume |

---

## ⚙️ Configuration

Edit `.env` file to configure:

```bash
# Sync API
MAX_SYNC_CONCURRENCY=10        # Max concurrent sync requests
WORK_TIMEOUT_SECONDS=30        # Work execution timeout

# Async API
NUM_WORKERS=5                  # Number of background workers
MAX_QUEUE_SIZE=100             # Max queued jobs
MAX_CALLBACK_RETRIES=3         # Callback retry attempts

# Rate Limiting
RATE_LIMIT_REQUESTS=100        # Requests per window
RATE_LIMIT_WINDOW_SECONDS=60   # Rate limit window

# Security
ALLOWED_CALLBACK_SCHEMES=["http","https"]
BLOCK_PRIVATE_IPS=true
BLOCK_LOCALHOST=false
```

---

## 📁 Project Structure

```
sync-async/
├── app/                      # Main application
│   ├── main.py              # FastAPI app
│   ├── api/                 # API endpoints
│   ├── core/                # Business logic (work engine, schemas)
│   ├── db/                  # Database layer (SQLite, raw SQL)
│   ├── worker/              # Async processing (queue, workers, callbacks)
│   └── utils/               # Utilities (rate limiter, URL validator)
├── load_test/               # Load testing tools
│   ├── callback_server.py   # Callback receiver
│   └── runner.py            # Load test runner
├── scripts/                 # Utility scripts
│   └── init_db.py          # Database initialization
└── data/                    # Database storage
```

---

## 🔍 Key Features

- ✅ **Rate Limiting** - Token bucket algorithm (100 req/60s per IP)
- ✅ **URL Validation** - Blocks localhost and private IPs
- ✅ **Retry Logic** - Exponential backoff for callbacks
- ✅ **Metrics** - Request tracking, queue stats, performance metrics
- ✅ **Health Checks** - Database and worker status

---

## 🎓 What This Demonstrates

1. **Concurrency Patterns**
   - Sync: Semaphore-based limiting
   - Async: Queue + worker pool

2. **Performance Under Load**
   - Sync: Degrades gracefully (high latency)
   - Async: Maintains responsiveness (fast acks)

3. **Trade-offs**
   - Sync: Simple but limited throughput
   - Async: Complex but high throughput

---

## 🛠️ Tech Stack

- **Python 3.11+**
- **FastAPI** - Modern async web framework
- **Pydantic** - Data validation
- **SQLite** - Lightweight database
- **aiosqlite** - Async SQLite driver
- **httpx** - Async HTTP client
- **asyncio** - Async programming

---

## 📚 Additional Resources

- **Interactive API Docs:** http://localhost:8000/docs

---

## 🎯 Use Cases

**When to use Sync API:**
- Low request volume (<10 req/sec)
- Need immediate results
- Simple client implementation
- Short processing time (<1s)

**When to use Async API:**
- High request volume (>50 req/sec)
- Can wait for results
- Long processing time (>1s)
- Need to absorb traffic bursts

---

**Built with FastAPI, Python, and asyncio**
