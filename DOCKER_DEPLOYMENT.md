# Docker Deployment Guide

## Overview

The LeanIX Survey Creator is containerized with a **2-service architecture**:
- **FastAPI Backend** (port 8000)
- **Streamlit Frontend** (port 8502)

Both services are orchestrated using `docker-compose` for seamless deployment.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  Docker Compose Network                  │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────────┐          ┌──────────────────┐    │
│  │  leanix-api      │          │ leanix-frontend  │    │
│  │  (FastAPI)       │◄────────►│  (Streamlit)     │    │
│  │  Port 8000       │ HTTP     │  Port 8502       │    │
│  │  Health: /health │          │ Health: /_stcore/│    │
│  └──────────────────┘          └──────────────────┘    │
│         ▲                              ▲                │
│         │ Docker Bridge Network        │                │
│         └──────────────┬───────────────┘                │
│                        │                                │
└────────────────────────┼────────────────────────────────┘
                         │
              ┌──────────┴──────────┐
              │   Host Ports        │
              ├─────────────────────┤
              │  localhost:8000     │
              │  localhost:8502     │
              └─────────────────────┘
```

---

## Prerequisites

- **Docker** 20.10+
- **Docker Compose** 1.29+
- **LeanIX API Token** (with appropriate permissions)

Check versions:
```bash
docker --version
docker compose version
```

---

## Quick Start

### 1. Clone & Configure

```bash
# Clone repository
git clone https://github.com/hlyl/Leanix_survey.git
cd Leanix_survey

# Create .env from template
cp .env.example .env

# Edit .env with your LeanIX credentials
nano .env
```

**Required .env variables:**
```env
LEANIX_URL=https://your-instance.leanix.net
LEANIX_API_TOKEN=your-token-here
LEANIX_WORKSPACE_ID=your-uuid-here
```

### 2. Build & Run

```bash
# Build images
docker compose build

# Start services
docker compose up -d

# Check status
docker compose ps
```

### 3. Access Services

- **Frontend**: http://localhost:8502
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### 4. Stop Services

```bash
# Stop services (keep containers)
docker compose stop

# Stop and remove containers
docker compose down

# Remove everything (containers + images)
docker compose down -v --rmi all
```

---

## Commands Reference

### Build & Deployment

```bash
# Build images
docker compose build

# Build specific service
docker compose build api
docker compose build frontend

# Build with no cache
docker compose build --no-cache

# Build and start
docker compose up -d

# Start in foreground (see logs)
docker compose up
```

### Monitoring

```bash
# View logs
docker compose logs

# Follow logs (live tail)
docker compose logs -f

# Logs for specific service
docker compose logs -f api
docker compose logs -f frontend

# View service status
docker compose ps

# Check health
docker compose ps --format="table {{.Names}}\t{{.Status}}"
```

### Maintenance

```bash
# Execute command in container
docker compose exec api sh
docker compose exec frontend sh

# Restart services
docker compose restart

# Restart specific service
docker compose restart api

# Remove stopped containers
docker compose rm

# Clean up dangling images
docker image prune
```

---

## Environment Variables

### Backend Service

| Variable | Description | Example |
|----------|-------------|---------|
| `LEANIX_URL` | LeanIX instance URL | `https://instance.leanix.net` |
| `LEANIX_API_TOKEN` | API Bearer token | `your-token` |
| `LEANIX_WORKSPACE_ID` | Workspace UUID | `12345678-1234-...` |
| `LOG_LEVEL` | Logging level | `INFO`, `DEBUG`, `WARNING` |
| `CACHE_ENABLED` | Enable caching | `true`, `false` |
| `MAX_BATCH_SIZE` | Max batch requests | `25`, `50` |
| `API_TIMEOUT` | Request timeout (sec) | `30` |

### Frontend Service

| Variable | Description | Example |
|----------|-------------|---------|
| `BACKEND_URL` | Backend API URL | `http://api:8000` |
| `LOG_LEVEL` | Logging level | `INFO`, `DEBUG` |
| `STREAMLIT_SERVER_HEADLESS` | Headless mode | `true` |

---

## Networking

Services communicate via Docker bridge network `leanix-network`:

```
Frontend → Backend: http://api:8000
```

**External access:**
- Frontend: `localhost:8502` (user-facing)
- Backend: `localhost:8000` (API + docs)

---

## Health Checks

Each service has health checks configured:

### Backend Health Check
```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "ok",
  "version": "1.1.0"
}
```

### Frontend Health Check
```bash
curl http://localhost:8502/_stcore/health
```

**Response:** `200 OK`

---

## Volumes

Services mount source code as read-only:

```yaml
volumes:
  - ./src:/app/src:ro           # Source code
  - ./examples:/app/examples:ro # Example surveys
```

For development, remove `:ro` to allow hot-reload:
```yaml
volumes:
  - ./src:/app/src              # Writable for development
```

---

## Troubleshooting

### "Cannot connect to Docker daemon"
```bash
# Start Docker service
sudo systemctl start docker

# Add user to docker group (Linux)
sudo usermod -aG docker $USER
```

### "Port already in use"
```bash
# Check what's using port 8000
lsof -i :8000

# Change port in docker-compose.yml
ports:
  - "8001:8000"  # Use 8001 instead
```

### "Service unhealthy"
```bash
# Check logs
docker compose logs -f api
docker compose logs -f frontend

# Restart service
docker compose restart api
```

### "Module not found" errors
```bash
# Rebuild image (fresh dependencies)
docker compose build --no-cache

# Restart services
docker compose restart
```

### "Connection refused" between services
```bash
# Ensure services are on same network
docker network ls
docker network inspect leanix-network

# Check service hostnames resolve
docker compose exec frontend ping api

# Verify BACKEND_URL environment variable
docker compose exec frontend env | grep BACKEND_URL
```

---

## Production Deployment

### Docker Hub Registry

```bash
# Tag image
docker tag leanix-api:latest myregistry/leanix-api:1.1.0
docker tag leanix-frontend:latest myregistry/leanix-frontend:1.1.0

# Push to registry
docker push myregistry/leanix-api:1.1.0
docker push myregistry/leanix-frontend:1.1.0

# Pull and run
docker compose pull
docker compose up -d
```

### Production docker-compose.yml

For production, use:
```yaml
services:
  api:
    image: myregistry/leanix-api:1.1.0  # Pre-built image
    restart: always
    # ... other settings

  frontend:
    image: myregistry/leanix-frontend:1.1.0
    restart: always
    # ... other settings
```

### Environment Management

Use separate `.env` files:
```bash
# Development
docker compose --env-file .env.dev up

# Production
docker compose --env-file .env.prod up -d
```

---

## Performance Optimization

### Build Optimization

```bash
# Use BuildKit (faster builds)
export DOCKER_BUILDKIT=1
docker compose build

# Multi-stage builds (done in Dockerfiles)
```

### Runtime Optimization

```yaml
# Limit resources
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
```

---

## Scaling

Scale services horizontally:

```bash
# Scale backend to 3 instances
docker compose up -d --scale api=3

# Note: Frontend typically remains 1 instance
```

For production scaling, use **Kubernetes** or similar orchestration.

---

## Security Best Practices

1. **Never commit .env** - Add to `.gitignore`
2. **Use secrets** - Docker Secrets / Kubernetes Secrets for production
3. **Limit permissions** - Use `:ro` volumes for immutable files
4. **Health checks** - Enabled and monitored
5. **Network isolation** - Services on private bridge network
6. **Read-only root** - Consider `--read-only` in production

---

## Logs & Debugging

### View All Logs
```bash
docker compose logs
```

### Real-time Logs
```bash
docker compose logs -f --tail=50
```

### Export Logs
```bash
docker compose logs > logs.txt
```

### Debug Container
```bash
# Shell into container
docker compose exec api bash
docker compose exec frontend bash

# Check environment
docker compose exec api env
```

---

## Files Reference

| File | Purpose |
|------|---------|
| `Dockerfile.api` | FastAPI backend image |
| `Dockerfile.streamlit` | Streamlit frontend image |
| `docker-compose.yml` | Service orchestration |
| `.dockerignore` | Docker build exclusions |
| `.env.example` | Environment template |
| `.env` | Environment secrets (not committed) |

---

## Cleanup

```bash
# Remove everything
docker compose down -v --rmi all

# Clean up unused images/volumes
docker system prune -a --volumes
```

---

## Additional Resources

- [Docker Documentation](https://docs.docker.com)
- [Docker Compose Docs](https://docs.docker.com/compose/)
- [FastAPI in Docker](https://fastapi.tiangolo.com/deployment/docker/)
- [Streamlit in Docker](https://docs.streamlit.io/knowledge-base/tutorials/deploy/docker)

---

**Status:** ✅ Production-Ready

**Last Updated:** January 17, 2026
