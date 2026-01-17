# Deployment Guide - LeanIX Survey Creator

This guide covers deploying the LeanIX Survey Creator to production environments.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Deployment](#local-deployment)
3. [Docker Deployment](#docker-deployment)
4. [Cloud Deployments](#cloud-deployments)
5. [Monitoring & Logging](#monitoring--logging)
6. [Troubleshooting](#troubleshooting)

## Prerequisites

- Python 3.12+ (or Docker)
- UV package manager (or pip)
- LeanIX instance with API access
- API token with survey creation permissions

## Local Deployment

### 1. Setup Environment

```bash
# Clone repository
git clone <repository-url>
cd leanix-survey-creator

# Create virtual environment
uv venv

# Activate environment
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate  # Windows

# Install dependencies
uv pip install -e .
```

### 2. Configure Environment

Create `.env` file:
```bash
# LeanIX Configuration
LEANIX_URL=https://your-instance.leanix.net
LEANIX_API_TOKEN=your-api-token-here
LEANIX_WORKSPACE_ID=your-workspace-uuid

# API Configuration
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8501
LOG_LEVEL=INFO

# Optional
API_TIMEOUT=30
```

### 3. Run Applications

**Streamlit UI** (development):
```bash
streamlit run streamlit_app.py
```

Access at: `http://localhost:8501`

**FastAPI Backend**:
```bash
uvicorn api:app --host 127.0.0.1 --port 8000
```

Access at: `http://localhost:8000/docs` (API docs)

## Docker Deployment

### 1. Build Docker Image

Create `Dockerfile`:
```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install UV
RUN pip install --no-cache-dir uv

# Copy project files
COPY . .

# Install dependencies
RUN uv pip install --system -e .

# Expose ports
EXPOSE 8000 8501

# Run both services
CMD ["sh", "-c", "uvicorn api:app --host 0.0.0.0 --port 8000 & streamlit run streamlit_app.py --server.port=8501 --server.address=0.0.0.0"]
```

Build image:
```bash
docker build -t leanix-survey-creator:latest .
```

### 2. Docker Compose

Create `docker-compose.yml`:
```yaml
version: '3.8'

services:
  api:
    image: leanix-survey-creator:latest
    ports:
      - "8000:8000"
    environment:
      - LEANIX_URL=${LEANIX_URL}
      - LEANIX_API_TOKEN=${LEANIX_API_TOKEN}
      - LEANIX_WORKSPACE_ID=${LEANIX_WORKSPACE_ID}
      - ALLOWED_ORIGINS=${ALLOWED_ORIGINS}
      - LOG_LEVEL=${LOG_LEVEL}
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/"]
      interval: 30s
      timeout: 10s
      retries: 3

  streamlit:
    image: leanix-survey-creator:latest
    ports:
      - "8501:8501"
    environment:
      - LEANIX_URL=${LEANIX_URL}
      - LEANIX_API_TOKEN=${LEANIX_API_TOKEN}
      - LEANIX_WORKSPACE_ID=${LEANIX_WORKSPACE_ID}
      - LOG_LEVEL=${LOG_LEVEL}
    restart: unless-stopped
    depends_on:
      - api
```

Create `.env` file with required variables, then run:
```bash
docker-compose up -d
```

## Cloud Deployments

### AWS Deployment (ECS)

#### 1. Push to ECR

```bash
# Authenticate with ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

# Tag image
docker tag leanix-survey-creator:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/leanix-survey-creator:latest

# Push image
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/leanix-survey-creator:latest
```

#### 2. ECS Task Definition

Create `task-definition.json`:
```json
{
  "family": "leanix-survey-creator",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "containerDefinitions": [
    {
      "name": "api",
      "image": "<account-id>.dkr.ecr.us-east-1.amazonaws.com/leanix-survey-creator:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "hostPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "LEANIX_URL",
          "value": "https://your-instance.leanix.net"
        }
      ],
      "secrets": [
        {
          "name": "LEANIX_API_TOKEN",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:<account-id>:secret:leanix/api-token"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/leanix-survey-creator",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

Register task:
```bash
aws ecs register-task-definition --cli-input-json file://task-definition.json
```

#### 3. Create ECS Service

```bash
aws ecs create-service \
  --cluster leanix-surveys \
  --service-name leanix-survey-api \
  --task-definition leanix-survey-creator:1 \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}" \
  --load-balancers targetGroupArn=arn:aws:elasticloadbalancing:us-east-1:<account-id>:targetgroup/leanix-surveys/xxx,containerName=api,containerPort=8000
```

### Google Cloud Run Deployment

#### 1. Deploy to Cloud Run

```bash
# Authenticate
gcloud auth login

# Build and deploy
gcloud run deploy leanix-survey-creator \
  --source . \
  --platform managed \
  --region us-central1 \
  --memory 1Gi \
  --timeout 600 \
  --set-env-vars LEANIX_URL=https://your-instance.leanix.net,ALLOWED_ORIGINS=https://surveys.example.com \
  --set-secrets LEANIX_API_TOKEN=leanix-api-token:latest,LEANIX_WORKSPACE_ID=leanix-workspace-id:latest
```

#### 2. Create Secrets

```bash
echo -n "your-api-token-here" | gcloud secrets create leanix-api-token --data-file=-
echo -n "your-workspace-uuid" | gcloud secrets create leanix-workspace-id --data-file=-
```

### Azure App Service Deployment

#### 1. Create Container Registry

```bash
az acr create --resource-group myResourceGroup --name myRegistry --sku Basic

# Build and push
az acr build --registry myRegistry --image leanix-survey-creator:latest .
```

#### 2. Create App Service

```bash
az webapp create \
  --resource-group myResourceGroup \
  --plan myAppServicePlan \
  --name leanix-survey-creator \
  --deployment-container-image-name myRegistry.azurecr.io/leanix-survey-creator:latest
```

#### 3. Configure Environment Variables

```bash
az webapp config appsettings set \
  --resource-group myResourceGroup \
  --name leanix-survey-creator \
  --settings LEANIX_URL=https://your-instance.leanix.net \
  --settings ALLOWED_ORIGINS=https://surveys.example.com
```

## Production Architecture

### Recommended Setup

```
┌─────────────────────────────────────────────────────────┐
│                     Users/Clients                        │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────▼────────────┐
        │   DNS / Load Balancer   │
        │   (Route 53 / ALB)      │
        └────────────┬────────────┘
                     │
        ┌────────────▼────────────────────┐
        │   Reverse Proxy / WAF           │
        │   (Nginx / CloudFront / WAF)    │
        └────────────┬────────────────────┘
                     │
        ┌────────────▼────────────────────┐
        │  API Container Cluster          │
        │  - FastAPI (uvicorn)            │
        │  - Streamlit (optional)         │
        │  - Auto-scaling enabled         │
        └────────────┬────────────────────┘
                     │
        ┌────────────▼────────────────────┐
        │   Logging & Monitoring          │
        │   (CloudWatch / ELK / Datadog)  │
        └─────────────────────────────────┘
```

### Reverse Proxy Configuration

Use Nginx as reverse proxy:

```nginx
upstream api_backend {
    least_conn;
    server app1:8000;
    server app2:8000;
    server app3:8000;
}

server {
    listen 443 ssl http2;
    server_name api.surveys.acme.com;
    
    # TLS Configuration
    ssl_certificate /etc/letsencrypt/live/api.surveys.acme.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.surveys.acme.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Rate Limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # API Routes
    location /api/ {
        limit_req zone=api_limit burst=20 nodelay;
        
        proxy_pass http://api_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Health Check
    location /health {
        access_log off;
        proxy_pass http://api_backend;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name api.surveys.acme.com;
    return 301 https://$server_name$request_uri;
}
```

## Monitoring & Logging

### Application Monitoring

Monitor these metrics:
- API response times
- Error rates
- Request throughput
- Memory usage
- CPU usage
- Disk space

### Example: Prometheus Metrics

Add to your monitoring:
```python
from prometheus_client import Counter, Histogram, generate_latest

survey_creates = Counter('survey_creates_total', 'Total surveys created')
survey_errors = Counter('survey_errors_total', 'Total survey creation errors')
api_latency = Histogram('api_latency_seconds', 'API latency in seconds')
```

### Logging Configuration

**Log Levels**:
- `DEBUG`: Detailed diagnostic information (development)
- `INFO`: General operational information (production)
- `WARNING`: Warning messages (production)
- `ERROR`: Error messages (all)

**Recommended Log Aggregation**:
- ELK Stack (Elasticsearch, Logstash, Kibana)
- Datadog
- CloudWatch
- Splunk

## Troubleshooting

### Container won't start

**Check logs**:
```bash
docker logs <container-id>
```

**Common issues**:
- Missing environment variables
- Port already in use
- Invalid API token
- Network connectivity issues

### High memory usage

**Solutions**:
- Increase container memory limit
- Enable log rotation
- Configure garbage collection
- Monitor for memory leaks

### API timeouts

**Solutions**:
- Increase `API_TIMEOUT` environment variable
- Check LeanIX instance availability
- Verify network connectivity
- Check for rate limiting

### Authorization failures

**Check**:
- API token validity in LeanIX
- Token permissions in LeanIX admin
- Workspace ID validity
- CORS configuration

### Certificate issues

**Resolution**:
```bash
# Verify certificate
openssl x509 -in /etc/letsencrypt/live/api.surveys.acme.com/cert.pem -noout -text

# Renew certificate
certbot renew --force-renewal
```

## Health Checks

**API Health Endpoint**:
```bash
curl https://api.surveys.acme.com/

# Expected response:
# {"service": "LeanIX Survey Creator", "version": "1.0.0", ...}
```

## Rollback Procedures

### Blue-Green Deployment

```bash
# Deploy new version to "green"
docker-compose -f docker-compose.green.yml up -d

# Test green environment
curl http://localhost:8001/

# Switch traffic to green (via load balancer)
# If issues, switch back to blue (current production)
```

### Versioning

Tag images with versions:
```bash
docker tag leanix-survey-creator:latest leanix-survey-creator:v1.2.3
docker push <registry>/leanix-survey-creator:v1.2.3

# Rollback to previous version
docker run <registry>/leanix-survey-creator:v1.2.2
```
