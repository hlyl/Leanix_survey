"""
API Endpoints Documentation

This document describes all available API endpoints in the LeanIX Survey Creator backend.
"""

# API Endpoints Documentation

## Base URL

- **Development**: `http://localhost:8000`
- **Environment**: Set `BACKEND_URL` environment variable to override

## Authentication

All endpoints that interact with LeanIX require three query parameters:
- `leanix_url`: Your LeanIX instance URL (e.g., `https://your-instance.leanix.net`)
- `api_token`: LeanIX API token with poll creation permissions
- `workspace_id`: UUID of the target workspace

## Endpoints

### 1. Health Check

**GET** `/health`

Check if the API is running and healthy.

**Response:**
```json
{
  "status": "healthy"
}
```

---

### 2. Root Information

**GET** `/`

Get API service information and available endpoints.

**Response:**
```json
{
  "service": "LeanIX Survey Creator",
  "version": "1.0.0",
  "endpoints": {
    "validate": "/api/validate",
    "create": "/api/surveys/create"
  }
}
```

---

### 3. Validate Survey

**POST** `/api/validate`

Validate a survey definition without creating it. Accepts raw JSON string and validates against the SurveyInput schema.

**Request Body:**
```json
{
  "json_input": "{\"title\": \"...\", \"questionnaire\": {...}}"
}
```

**Response (Valid):**
```json
{
  "valid": true,
  "message": "Survey definition is valid",
  "survey_input": {
    "title": "My Survey",
    "questionnaire": {...},
    ...
  },
  "details": {
    "title": "My Survey",
    "question_count": 5,
    "has_user_query": true,
    "has_fact_sheet_query": false
  },
  "error": null
}
```

**Response (Invalid):**
```json
{
  "valid": false,
  "message": "Validation failed",
  "survey_input": null,
  "error": "Field 'title' is required",
  "details": null
}
```

---

### 4. Create Survey

**POST** `/api/surveys/create?leanix_url=...&api_token=...&workspace_id=...`

Create a single survey in LeanIX.

**Request Body:**
```json
{
  "survey_input": {
    "title": "Q1 Application Health Check",
    "questionnaire": {
      "questions": [...]
    },
    ...
  },
  "language": "en",
  "fact_sheet_type": "Application",
  "due_date": "2024-12-31"
}
```

**Response (Success):**
```json
{
  "success": true,
  "poll_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Survey created successfully in LeanIX",
  "errors": null
}
```

**Response (Failure):**
```json
{
  "success": false,
  "poll_id": null,
  "message": "Failed to create survey: ...",
  "errors": ["error message"]
}
```

---

### 5. Create Surveys (Batch)

**POST** `/api/surveys/create-batch?leanix_url=...&api_token=...&workspace_id=...`

Create multiple surveys in a single request with optional fail-fast behavior.

**Query Parameters:**
- `leanix_url`: LeanIX instance URL
- `api_token`: API token
- `workspace_id`: Workspace UUID

**Request Body:**
```json
{
  "requests": [
    {
      "survey_input": {...},
      "language": "en",
      "fact_sheet_type": "Application",
      "due_date": null
    },
    {
      "survey_input": {...},
      "language": "de",
      "fact_sheet_type": "Application",
      "due_date": "2024-12-31"
    }
  ],
  "fail_fast": true
}
```

**Parameters:**
- `requests`: Array of survey creation requests (max size: `MAX_BATCH_SIZE`, default 25)
- `fail_fast`: If true, stops processing after the first error (default: true)

**Response:**
```json
{
  "success": true,
  "succeeded": 2,
  "failed": 0,
  "results": [
    {
      "index": 0,
      "success": true,
      "poll_id": "550e8400-e29b-41d4-a716-446655440000",
      "message": "Survey created successfully",
      "errors": null
    },
    {
      "index": 1,
      "success": true,
      "poll_id": "550e8400-e29b-41d4-a716-446655440001",
      "message": "Survey created successfully",
      "errors": null
    }
  ],
  "message": "Batch completed: 2 succeeded, 0 failed"
}
```

**Error Response (Exceeds Max Batch Size):**
```json
{
  "detail": "Batch size exceeds maximum of 25"
}
```

---

### 6. Retrieve Survey (Poll)

**GET** `/api/surveys/{poll_id}?leanix_url=...&api_token=...&workspace_id=...`

Retrieve a poll definition from LeanIX by ID.

**Path Parameters:**
- `poll_id`: UUID of the poll to retrieve

**Query Parameters:**
- `leanix_url`: LeanIX instance URL
- `api_token`: API token
- `workspace_id`: Workspace UUID

**Response:**
```json
{
  "status": "OK",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "Q1 Application Health Check",
    "language": "en",
    "questionnaire": {...},
    ...
  }
}
```

**Response (Not Found):**
```json
{
  "detail": "Poll not found or access denied"
}
```

---

## Environment Variables

### Runtime Configuration

- **`ALLOWED_ORIGINS`**: Comma-separated CORS origins (default: `http://localhost:3000,http://localhost:8501`)
- **`LOG_LEVEL`**: Logging level (default: `INFO`)
- **`API_TIMEOUT`**: Request timeout in seconds (default: `30`)
- **`MAX_CONNECTIONS`**: Maximum concurrent connections (default: `10`)
- **`MAX_KEEPALIVE_CONNECTIONS`**: Maximum keepalive connections (default: `5`)

### Batch Configuration

- **`MAX_BATCH_SIZE`**: Maximum surveys per batch request (default: `25`)

### Caching Configuration

- **`CACHE_ENABLED`**: Enable poll response caching (default: `false`)
- **`CACHE_TTL_SECONDS`**: Cache time-to-live in seconds (default: `300`)
- **`CACHE_MAX_ITEMS`**: Maximum cached poll responses (default: `128`)

### Frontend Configuration

- **`BACKEND_URL`**: Backend API URL for Streamlit UI (default: `http://localhost:8000`)

---

## Error Handling

### Common Error Responses

**422 Unprocessable Entity:**
```json
{
  "detail": "Invalid configuration: URL must use http or https, Invalid URL format"
}
```

**400 Bad Request:**
```json
{
  "detail": "Batch requests cannot be empty"
}
```

**404 Not Found:**
```json
{
  "detail": "Poll not found or access denied"
}
```

**503 Service Unavailable:**
```json
{
  "detail": "Failed to connect to LeanIX: connection error"
}
```

---

## Performance Considerations

### HTTP Client Pooling

- Shared AsyncClient with connection pooling
- Configurable connection limits and keepalive settings
- Automatic retry on transient failures (3 attempts)
- Timeout protection for all requests

### Caching

When `CACHE_ENABLED=true`:
- Poll responses cached by `workspace_id:poll_id` key
- TTL-based expiration (configurable)
- Thread-safe cache with async locking
- Improves performance for repeated poll retrievals

### Batch Processing

- Fail-fast mode stops processing after first error
- Batch size limited to prevent resource exhaustion
- Per-item error handling preserves partial results
- Suitable for bulk survey creation workflows

---

## Rate Limiting

No built-in rate limiting. Recommendations:
- Batch operations instead of repeated single requests
- Use appropriate timeouts to prevent hanging connections
- Implement client-side rate limiting for public-facing APIs

---

## Usage Examples

### Create a Single Survey

```bash
curl -X POST "http://localhost:8000/api/surveys/create" \
  -H "Content-Type: application/json" \
  -d '{
    "survey_input": {"title": "...", "questionnaire": {...}},
    "language": "en",
    "fact_sheet_type": "Application"
  }' \
  -G --data-urlencode "leanix_url=https://your-instance.leanix.net" \
     --data-urlencode "api_token=your-token" \
     --data-urlencode "workspace_id=your-workspace-uuid"
```

### Validate Survey JSON

```bash
curl -X POST "http://localhost:8000/api/validate" \
  -H "Content-Type: application/json" \
  -d '{"json_input": "{\"title\": \"...\", \"questionnaire\": {...}}"}'
```

### Create Batch with Fail-Fast

```bash
curl -X POST "http://localhost:8000/api/surveys/create-batch" \
  -H "Content-Type: application/json" \
  -d '{
    "requests": [{...}, {...}],
    "fail_fast": true
  }' \
  -G --data-urlencode "leanix_url=..." \
     --data-urlencode "api_token=..." \
     --data-urlencode "workspace_id=..."
```

### Retrieve Poll with Caching

```bash
# Enable caching via environment
export CACHE_ENABLED=true
export CACHE_TTL_SECONDS=600

curl "http://localhost:8000/api/surveys/550e8400-e29b-41d4-a716-446655440000" \
  -G --data-urlencode "leanix_url=..." \
     --data-urlencode "api_token=..." \
     --data-urlencode "workspace_id=..."
```
