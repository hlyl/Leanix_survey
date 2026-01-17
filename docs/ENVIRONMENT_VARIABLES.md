# Environment Variables Reference

This document lists all configurable environment variables for the LeanIX Survey Creator.

## Backend (FastAPI API)

### Logging

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `LOG_LEVEL` | string | `INFO` | Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL |

### CORS Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `ALLOWED_ORIGINS` | comma-separated list | `http://localhost:3000,http://localhost:8501` | CORS allowed origins |

### HTTP Client Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `API_TIMEOUT` | float (seconds) | `30` | Request timeout for LeanIX API calls |
| `MAX_CONNECTIONS` | int | `10` | Maximum concurrent HTTP connections in pool |
| `MAX_KEEPALIVE_CONNECTIONS` | int | `5` | Maximum keepalive connections in pool |

### Batch Processing

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `MAX_BATCH_SIZE` | int | `25` | Maximum number of surveys in a batch request |

### Response Caching

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `CACHE_ENABLED` | boolean | `false` | Enable poll response caching (true/false) |
| `CACHE_TTL_SECONDS` | int | `300` | Cache entry time-to-live in seconds |
| `CACHE_MAX_ITEMS` | int | `128` | Maximum number of cached poll responses |

---

## Frontend (Streamlit UI)

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `BACKEND_URL` | URL | `http://localhost:8000` | Backend API URL |
| `LOG_LEVEL` | string | `INFO` | Logging level for Streamlit app |

---

## Configuration Examples

### Development Environment

Minimal configuration for local development:

```bash
# .env or shell
export ALLOWED_ORIGINS="http://localhost:3000,http://localhost:8501"
export LOG_LEVEL="DEBUG"
export BACKEND_URL="http://localhost:8000"
```

### Production Environment with Caching

Configuration for production with performance optimizations:

```bash
export ALLOWED_ORIGINS="https://app.example.com,https://ui.example.com"
export LOG_LEVEL="INFO"
export API_TIMEOUT="60"
export MAX_CONNECTIONS="20"
export MAX_KEEPALIVE_CONNECTIONS="10"
export MAX_BATCH_SIZE="50"
export CACHE_ENABLED="true"
export CACHE_TTL_SECONDS="600"
export CACHE_MAX_ITEMS="256"
export BACKEND_URL="https://api.example.com"
```

### High-Performance Batch Mode

Configuration optimized for batch operations:

```bash
export MAX_BATCH_SIZE="100"
export API_TIMEOUT="90"
export MAX_CONNECTIONS="30"
export MAX_KEEPALIVE_CONNECTIONS="15"
export CACHE_ENABLED="false"  # Reduce memory usage
```

### Caching-Optimized Mode

Configuration for read-heavy workloads:

```bash
export CACHE_ENABLED="true"
export CACHE_TTL_SECONDS="1800"    # 30 minutes
export CACHE_MAX_ITEMS="512"       # More items
export API_TIMEOUT="30"
export MAX_CONNECTIONS="5"         # Fewer connections needed
```

### Testing Environment

Configuration for integration tests:

```bash
export LOG_LEVEL="DEBUG"
export CACHE_ENABLED="false"
export API_TIMEOUT="10"
export ALLOWED_ORIGINS="http://localhost:*"
```

---

## Setting Environment Variables

### Using `.env` File

Create a `.env` file in the project root:

```bash
# .env
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8501
LOG_LEVEL=INFO
API_TIMEOUT=30
MAX_BATCH_SIZE=25
CACHE_ENABLED=false
```

### Using Environment

```bash
# Shell export
export LOG_LEVEL=DEBUG
export API_TIMEOUT=60

# Command line
LOG_LEVEL=DEBUG API_TIMEOUT=60 uvicorn api:app

# Docker
docker run -e LOG_LEVEL=DEBUG -e API_TIMEOUT=60 leanix-survey:latest
```

### Using Python-Dotenv

```python
from dotenv import load_dotenv
load_dotenv()  # Loads from .env

# Access variables
import os
log_level = os.getenv("LOG_LEVEL", "INFO")
```

---

## Variable Type Conversions

### Boolean Variables

Accepted values:
- **True**: `true`, `True`, `1`, `yes`
- **False**: `false`, `False`, `0`, `no`

Example:
```bash
# These are all equivalent to true
CACHE_ENABLED=true
CACHE_ENABLED=True
CACHE_ENABLED=1
```

### Numeric Variables

Automatically converted to int or float:

```bash
# Integer
MAX_BATCH_SIZE=25

# Float with seconds
API_TIMEOUT=30.5
CACHE_TTL_SECONDS=300

# Automatic conversion happens in app startup
```

### List Variables

Comma-separated values are split:

```bash
# Single origin
ALLOWED_ORIGINS=http://localhost:3000

# Multiple origins
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8501,https://app.example.com
```

---

## Validation and Constraints

### Recommended Ranges

| Variable | Min | Max | Notes |
|----------|-----|-----|-------|
| `API_TIMEOUT` | 5 | 300 | Seconds, LeanIX API varies |
| `MAX_CONNECTIONS` | 1 | 100 | Server-dependent resource limit |
| `MAX_KEEPALIVE_CONNECTIONS` | 1 | 50 | Usually ≤ MAX_CONNECTIONS |
| `MAX_BATCH_SIZE` | 1 | 1000 | Memory and performance impact |
| `CACHE_TTL_SECONDS` | 0 | 86400 | 0 = disabled, 24h = 86400 |
| `CACHE_MAX_ITEMS` | 1 | 10000 | Memory-based limit |

### Default Behavior if Not Set

| Variable | Fallback |
|----------|----------|
| `LOG_LEVEL` | `INFO` |
| `ALLOWED_ORIGINS` | Development defaults |
| `API_TIMEOUT` | `30` seconds |
| `MAX_CONNECTIONS` | `10` |
| `MAX_KEEPALIVE_CONNECTIONS` | `5` |
| `MAX_BATCH_SIZE` | `25` |
| `CACHE_ENABLED` | `false` |
| `CACHE_TTL_SECONDS` | `300` |
| `CACHE_MAX_ITEMS` | `128` |
| `BACKEND_URL` | `http://localhost:8000` |

---

## Performance Tuning Guide

### For Slow Networks

```bash
export API_TIMEOUT=60           # More time for requests
export MAX_KEEPALIVE_CONNECTIONS=3  # Fewer persistent connections
```

### For Fast Networks with Many Requests

```bash
export API_TIMEOUT=15           # Faster timeout
export MAX_CONNECTIONS=30       # More concurrent requests
export MAX_BATCH_SIZE=100       # Larger batches
```

### For Memory Constrained Environments

```bash
export CACHE_ENABLED=false      # No caching
export MAX_CONNECTIONS=3        # Minimal pool
export MAX_BATCH_SIZE=10        # Smaller batches
```

### For High-Throughput Scenarios

```bash
export MAX_CONNECTIONS=50
export MAX_KEEPALIVE_CONNECTIONS=20
export MAX_BATCH_SIZE=100
export CACHE_ENABLED=true
export CACHE_TTL_SECONDS=300
export CACHE_MAX_ITEMS=512
```

---

## Troubleshooting

### "Connection refused" errors

Check timeout and connection limits:
```bash
export API_TIMEOUT=60
export MAX_CONNECTIONS=20
```

### "Out of memory" errors

Reduce caching:
```bash
export CACHE_ENABLED=false
# or
export CACHE_MAX_ITEMS=64
```

### Slow response times

Enable caching and increase connections:
```bash
export CACHE_ENABLED=true
export MAX_CONNECTIONS=20
```

### CORS errors in frontend

Verify ALLOWED_ORIGINS includes frontend URL:
```bash
export ALLOWED_ORIGINS="http://localhost:3000,http://localhost:8501,https://your-frontend.com"
```

---

## See Also

- [API Documentation](API_DOCUMENTATION.md) - Endpoint details
- [Features](FEATURES.md) - Feature descriptions
- [Deployment Guide](DEPLOYMENT.md) - Production deployment
- [Security Guide](SECURITY.md) - Security best practices
