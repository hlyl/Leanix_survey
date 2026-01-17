# Security Guide - LeanIX Survey Creator

This document describes security best practices and hardening recommendations for the LeanIX Survey Creator.

## Table of Contents

1. [Critical Security Issues](#critical-security-issues)
2. [Authentication & Authorization](#authentication--authorization)
3. [Network Security](#network-security)
4. [Data Protection](#data-protection)
5. [Secrets Management](#secrets-management)
6. [Input Validation](#input-validation)
7. [Security Checklist](#security-checklist)

## Critical Security Issues

### CORS Configuration

**Issue**: By default, CORS is restricted to local development origins.

**For Production**:
```bash
# Set allowed origins via environment variable
export ALLOWED_ORIGINS="https://your-domain.com,https://api.your-domain.com"
```

**Configuration Details**:
- `ALLOWED_ORIGINS`: Comma-separated list of allowed origins
- Default (development): `http://localhost:3000,http://localhost:8501`
- Production: Use your actual domain(s), never use `*`

**Example** (production setup):
```bash
ALLOWED_ORIGINS="https://surveys.acme.com,https://admin.acme.com" uvicorn api:app --host 0.0.0.0 --port 8000
```

### HTTP Methods Restriction

The API only allows specific HTTP methods:
- `GET`: For retrieving survey data
- `POST`: For creating surveys

All other methods are rejected at the middleware level.

## Authentication & Authorization

### API Token Security

⚠️ **Warning**: API tokens grant full access to your LeanIX instance. Treat them like passwords.

**Best Practices**:
1. **Never commit tokens** to version control
2. **Use environment variables** for token storage
3. **Rotate tokens regularly** (follow your organization's policy)
4. **Use least privilege** tokens (restrict permissions to minimum needed)
5. **Monitor token usage** in LeanIX audit logs

**Token Storage**:
```bash
# ✅ Good: Use environment variables
export LEANIX_API_TOKEN="your-token-here"
python api.py

# ❌ Bad: Hardcoded in code
api_token = "your-token-here"  # Don't do this!

# ❌ Bad: Committed to git
# .env file tracked in git (use .env.local and .gitignore)
```

### Streamlit Configuration

For production Streamlit deployments:

```toml
[client]
# Require password for Streamlit authentication
showErrorDetails = false

[server]
# Disable file uploader
maxUploadSize = 200

[logger]
level = "error"
```

## Network Security

### TLS/SSL

**For Production**:
1. **Always use HTTPS** - Never expose the API over plain HTTP
2. **Obtain valid certificates** - Use Let's Encrypt or your CA
3. **Configure strict TLS** - Use TLS 1.2+

**Nginx Reverse Proxy Example**:
```nginx
server {
    listen 443 ssl http2;
    server_name api.surveys.acme.com;
    
    ssl_certificate /etc/letsencrypt/live/api.surveys.acme.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.surveys.acme.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

server {
    listen 80;
    server_name api.surveys.acme.com;
    return 301 https://$server_name$request_uri;
}
```

### Rate Limiting

**Recommended**: Implement rate limiting at the reverse proxy or load balancer level.

**Nginx Example**:
```nginx
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

server {
    location /api/ {
        limit_req zone=api_limit burst=20 nodelay;
        proxy_pass http://localhost:8000;
    }
}
```

### Firewall Rules

**Restrict access** to the API and Streamlit services:
- Only allow necessary IP ranges
- Use security groups (AWS) or firewall rules (GCP/Azure)
- Whitelist LeanIX instance IPs if known

## Data Protection

### Input Validation

All inputs are validated:
- **URLs**: Protocol, format validation
- **UUIDs**: Format validation for workspace IDs
- **API Tokens**: Length and format checks
- **Survey Data**: Full Pydantic model validation

**Example**: Invalid input rejection
```python
# URL validation
❌ "not-a-url" -> Rejected
❌ "ftp://example.com" -> Rejected (not HTTP/HTTPS)
✓ "https://instance.leanix.net" -> Accepted

# UUID validation
❌ "not-a-uuid" -> Rejected
✓ "550e8400-e29b-41d4-a716-446655440000" -> Accepted
```

### Logging

**Security Events Logged**:
- Survey creation requests
- Failed validations
- Configuration errors
- Network/API errors

⚠️ **Important**: Logs may contain sensitive information
- Store logs securely
- Restrict access to log files
- Rotate logs regularly
- Never log API tokens

**Log Configuration**:
```bash
# Set appropriate log level
export LOG_LEVEL="INFO"  # or "WARNING" for production

# Configure log output
export LOG_FILE="/var/log/leanix-surveys/app.log"
```

## Secrets Management

### Environment Variables

**Required for Production**:
```bash
# LeanIX Configuration
LEANIX_URL=https://your-instance.leanix.net
LEANIX_API_TOKEN=your-token-here
LEANIX_WORKSPACE_ID=your-workspace-uuid

# API Security
ALLOWED_ORIGINS=https://your-domain.com
LOG_LEVEL=INFO

# Optional
API_TIMEOUT=30
```

### Docker Secrets (Recommended for Containers)

```bash
# Using Docker Swarm secrets
echo "your-token-here" | docker secret create leanix_api_token -

# In Docker Compose
docker run -e LEANIX_API_TOKEN_FILE=/run/secrets/leanix_api_token ...
```

### HashiCorp Vault (Enterprise)

```python
import hvac

client = hvac.Client(url="https://vault.example.com", token="your-token")
secret = client.secrets.kv.read_secret_version(path="leanix/prod")
api_token = secret['data']['data']['token']
```

### .env File Security

⚠️ **Never commit `.env` files to version control**

```bash
# Add to .gitignore
.env
.env.local
.env.*.local
secrets/

# Create .env.example with placeholder values
# Developers copy to .env and fill in their own values
```

## Input Validation

### Survey JSON Validation

All survey JSON is validated against the schema:
- Question types must be recognized
- Choice questions must have options
- Referenced question IDs must exist
- UUIDs must be valid format

### URL Validation

URLs are checked for:
- Valid HTTP/HTTPS scheme
- Valid domain format
- No trailing slashes
- Proper encoding

### UUID Validation

Workspace IDs must be valid UUIDs:
```python
# Valid formats
✓ "550e8400-e29b-41d4-a716-446655440000"
✓ "uuid.UUID" objects

# Invalid
❌ "not-a-uuid"
❌ "550e8400-e29b-41d4-a716-44665544000"  (missing digit)
```

## Security Checklist

### Pre-Production

- [ ] Change default `ALLOWED_ORIGINS` for production domain
- [ ] Obtain and configure TLS certificates
- [ ] Set up environment variables for all secrets
- [ ] Configure firewall rules and security groups
- [ ] Set up log rotation and storage
- [ ] Enable audit logging in LeanIX
- [ ] Test CORS restrictions
- [ ] Verify input validation is working
- [ ] Document token rotation procedure
- [ ] Set up monitoring and alerting

### Deployment

- [ ] Use HTTPS only (redirect HTTP to HTTPS)
- [ ] Use a reverse proxy (Nginx/Apache)
- [ ] Run API as non-root user
- [ ] Keep dependencies updated (`uv pip install --upgrade -e .`)
- [ ] Monitor application logs
- [ ] Set up rate limiting
- [ ] Enable HTTP security headers (Nginx/middleware)
- [ ] Use environment-specific configuration
- [ ] Test error handling doesn't leak sensitive info
- [ ] Backup configuration and secrets securely

### Ongoing

- [ ] Monitor security logs weekly
- [ ] Review and rotate API tokens quarterly
- [ ] Keep dependencies patched (security updates)
- [ ] Review access logs for suspicious activity
- [ ] Test disaster recovery procedures
- [ ] Conduct security audit annually
- [ ] Update documentation as policies change
- [ ] Train team on security best practices

## HTTP Security Headers

**Recommended headers** for Nginx/reverse proxy:

```nginx
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Content-Security-Policy "default-src 'self';" always;
```

## Incident Response

### If API Token is Compromised

1. **Immediately revoke** the token in LeanIX
2. **Generate a new token** with limited scope
3. **Update environment variables** across all deployments
4. **Review audit logs** for unauthorized activity
5. **Update secrets** in all systems (vault, Docker, etc.)
6. **Notify relevant teams** about the incident
7. **Document** the incident and response

### If Source Code is Leaked

1. **Revoke all API tokens** immediately
2. **Audit git history** for leaked secrets
3. **Use git-filter-repo** to remove from history
4. **Force push** (if private repository)
5. **Generate new tokens** and update deployment
6. **Notify security team** about the leak

## Support

For security questions or to report vulnerabilities, contact your security team.

**Do not** report security vulnerabilities in public issues.
