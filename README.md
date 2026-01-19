# LeanIX Survey Creator

A Python application for programmatically creating and managing LeanIX surveys with JSON-based definitions, Pydantic validation, Streamlit UI, and FastAPI backend.

## Features

- ✅ **JSON Schema Validation**: Comprehensive Pydantic models for survey definitions
- 🎯 **All Question Types**: Support for text, choice, date, number, and fact sheet mapping questions
- 🔗 **Conditional Logic**: Dependencies and nested questions
- 🌐 **Multi-language**: Support for multiple survey languages
- 🚀 **Streamlit UI**: User-friendly interface for survey creation
- 🔌 **FastAPI Backend**: RESTful API for integration
- 📦 **Batch Processing**: Create multiple surveys in a single request
- 💾 **Response Caching**: Optional TTL-based caching for poll retrievals
- 🔄 **Connection Pooling**: Shared HTTP client for improved performance
- 📊 **LeanIX Integration**: Direct API integration with LeanIX Poll API v2
- ✅ **Comprehensive Tests**: 36 unit and integration tests
- 🐳 **Docker Support**: Pre-built images published to GitHub Container Registry

## What's New in v1.1.0

- **Shared HTTP Client**: Pooled AsyncClient with connection reuse and timeouts
- **Batch Survey Creation**: Create up to 25 surveys (configurable) in one request with fail-fast options
- **Poll Response Caching**: Enable TTL-based caching for repeated poll retrievals
- **Improved Architecture**: Extracted `leanix_client.py` and `leanix_config.py` modules
- **Integration Tests**: 15 comprehensive integration tests covering all features
- **Enhanced Documentation**: API documentation, features guide, and environment variables reference

See [FEATURES.md](docs/FEATURES.md) for detailed information about new capabilities.

## Architecture

```
┌──────────────────────────────┐
│   Streamlit UI (Frontend)    │
└──────────────┬───────────────┘
               │
    ┌──────────▼──────────┐
    │  Backend API        │
    │  - Validation       │
    │  - Batch Creation   │
    │  - Caching          │
    │  - Shared Client    │
    └──────────┬──────────┘
               │
    ┌──────────▼──────────┐
    │  HTTP Client Pool   │
    │  (Connection Reuse) │
    └──────────┬──────────┘
               │
    ┌──────────▼──────────┐
    │  LeanIX Poll API    │
    │  (v2 Integration)   │
    └─────────────────────┘
```

## Project Structure

```
leanix-survey-creator/
├── leanix_survey_models.py          # Pydantic models and schemas
├── leanix_config.py                 # Configuration helpers (NEW)
├── leanix_client.py                 # Shared HTTP client (NEW)
├── api.py                           # FastAPI application
├── streamlit_app.py                 # Streamlit UI
├── validate_survey.py               # Validation utilities
├── generate_schema.py               # JSON Schema generator
├── test_models.py                   # Unit tests (21 tests)
├── tests/integration/               # Integration tests (15 tests)
│   └── test_api_integration.py
├── requirements.txt                 # Python dependencies
├── example_survey_*.json            # Survey examples
├── API_DOCUMENTATION.md             # API endpoint documentation (NEW)
├── FEATURES.md                      # Feature documentation (NEW)
├── ENVIRONMENT_VARIABLES.md         # Environment variables reference (NEW)
└── Makefile                         # Development commands
```

## Installation

### Using UV (Recommended)

This project uses **UV** for fast dependency management. See [docs/UV_SETUP.md](docs/UV_SETUP.md) for detailed instructions.

```bash
# Install UV (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment
uv venv

# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install project with dependencies
uv pip install -e .

# Or install with dev dependencies (includes pytest, ruff, black, mypy)
uv pip install -e ".[dev]"
```

### Using pip (Alternative)

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Using Docker (Production)

Pre-built Docker images are automatically published to GitHub Container Registry after successful tests.

**Pull and run with Docker Compose:**

```bash
# Pull latest images
docker pull ghcr.io/hlyl/leanix_survey-api:latest
docker pull ghcr.io/hlyl/leanix_survey-frontend:latest

# Create .env file with your credentials
cp .env.example .env
# Edit .env with your LeanIX configuration

# Run with pre-built images
docker compose -f docker-compose.yml up -d
```

**Available image tags:**
- `latest` - Latest stable build from main branch
- `1.0.0` - Specific version release
- `sha-<hash>` - Specific commit build

**For detailed Docker deployment instructions, see [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md)**

## Quick Start

### 1. Validate Survey JSON

```bash
python -m src.validate_survey examples/example_survey_simple.json
```

### 2. Run FastAPI Backend

```bash
python -m uvicorn src.api:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at http://localhost:8000

API documentation available at http://localhost:8000/docs

### 3. Run Streamlit UI

In a separate terminal:

```bash
streamlit run src/streamlit_app.py
```

Open http://localhost:8501 in your browser.

### 4. Use the API Directly

Create a single survey:

```bash
curl -X POST "http://localhost:8000/api/surveys/create" \
  -H "Content-Type: application/json" \
  -d '{
    "survey_input": {"title": "Test", "questionnaire": {"questions": [...]}},
    "language": "en",
    "fact_sheet_type": "Application"
  }' \
  -G --data-urlencode "leanix_url=https://your-instance.leanix.net" \
     --data-urlencode "api_token=your-token" \
     --data-urlencode "workspace_id=your-workspace-uuid"
```

Create multiple surveys (batch):

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

See [API_DOCUMENTATION.md](docs/API_DOCUMENTATION.md) for all endpoints.

## Configuration

### Environment Variables

Configure the backend behavior with environment variables:

```bash
# Logging
LOG_LEVEL=INFO

# Batch processing
MAX_BATCH_SIZE=25

# Performance
API_TIMEOUT=30
MAX_CONNECTIONS=10

# Caching
CACHE_ENABLED=true
CACHE_TTL_SECONDS=300
CACHE_MAX_ITEMS=128

# Frontend
BACKEND_URL=http://localhost:8000
```

See [docs/ENVIRONMENT_VARIABLES.md](docs/ENVIRONMENT_VARIABLES.md) for all configuration options and examples.

### Example: Enable Caching

```bash
CACHE_ENABLED=true \
CACHE_TTL_SECONDS=600 \
CACHE_MAX_ITEMS=256 \
python -m uvicorn api:app --host 0.0.0.0 --port 8000
```

### Example: High-Performance Batch Mode

```bash
MAX_BATCH_SIZE=100 \
MAX_CONNECTIONS=20 \
API_TIMEOUT=60 \
python -m uvicorn api:app --host 0.0.0.0 --port 8000
```
uvicorn api:app --reload
```

API will be available at http://localhost:8000

## Usage

### Creating a Survey via Streamlit

1. **Configure LeanIX Connection** (Sidebar)
   - Enter your LeanIX instance URL
   - Provide API token
   - Enter workspace ID

2. **Define Survey** (JSON Input tab)
   - Paste your survey JSON or load an example
   - Click "Validate JSON"

3. **Review** (Validation tab)
   - Check question details
   - Verify configuration

4. **Create** (Create Survey tab)
   - Set language, fact sheet type, and due date
   - Click "Create Survey in LeanIX"

### Survey JSON Schema

#### Minimal Example

```json
{
  "title": "Quick Check-in",
  "questionnaire": {
    "questions": [
      {
        "id": "q1",
        "label": "Is this application still active?",
        "type": "singlechoice",
        "options": [
          {"id": "yes", "label": "Yes"},
          {"id": "no", "label": "No"}
        ]
      }
    ]
  },
  "userQuery": {
    "roles": [
      {"subscriptionType": "RESPONSIBLE"}
    ]
  }
}
```

#### Comprehensive Example

See `example_survey_comprehensive.json` for:
- Multiple question types
- Conditional questions
- Validation rules
- User query configuration

### Question Types

| Type | Description | Example Use Case |
|------|-------------|------------------|
| `text` | Single-line text input | Name, short description |
| `textarea` | Multi-line text input | Comments, detailed descriptions |
| `singlechoice` | Select one option | Lifecycle status, priority |
| `multiplechoice` | Select multiple options | Tags, compliance requirements |
| `number` | Numeric input | Cost, user count |
| `date` | Date picker | Last review date, deadline |
| `factsheet` | Map to fact sheet field | Update lifecycle, tags directly |

### Conditional Questions

Questions can be shown/hidden based on parent question answers:

```json
{
  "id": "q2",
  "label": "Why is it being phased out?",
  "type": "textarea",
  "settings": {
    "isConditional": true,
    "dependency": {
      "parentId": "q1",
      "condition": {
        "phaseout": true
      }
    }
  }
}
```

### User Query Configuration

Define who receives the survey based on roles:

```json
{
  "userQuery": {
    "roles": [
      {
        "subscriptionType": "RESPONSIBLE"
      },
      {
        "subscriptionType": "ACCOUNTABLE"
      }
    ]
  }
}
```

**Subscription Types:**
- `RESPONSIBLE`: Users responsible for fact sheets
- `ACCOUNTABLE`: Users accountable for fact sheets
- `OBSERVER`: Users observing fact sheets
- `ALL`: All users with any subscription

### Fact Sheet Query Configuration

Select which fact sheets to include (alternative to user query):

```json
{
  "factSheetQuery": {
    "filter": {
      "fsType": "Application",
      "facetFilter": [
        {
          "facetKey": "lifecycle",
          "keys": ["active"],
          "operator": "OR"
        }
      ]
    }
  }
}
```

## Programmatic Usage

### Validating Survey JSON

```python
from validate_survey import validate_json_string

json_text = '{"title": "Test", ...}'
is_valid, survey_input, error_msg = validate_json_string(json_text)

if is_valid:
    print(f"Survey: {survey_input.title}")
    print(f"Questions: {len(survey_input.questionnaire.questions)}")
else:
    print(f"Error: {error_msg}")
```

### Creating a Survey

```python
from leanix_survey_models import SurveyInput, PollCreate
import httpx

# Load and validate
survey_input = SurveyInput.model_validate(json_data)

# Create poll request
poll_data = PollCreate.from_survey_input(
    survey_input=survey_input,
    language="en",
    fact_sheet_type="Application",
    due_date=None
)

# Send to LeanIX
headers = {
    "Authorization": f"Bearer {api_token}",
    "Content-Type": "application/json"
}

response = httpx.post(
    f"{leanix_url}/services/poll/v2/polls",
    params={"workspaceId": workspace_id},
    headers=headers,
    json=poll_data.model_dump(by_alias=True, exclude_none=True)
)

result = response.json()
poll_id = result["data"]["id"]
```

## Configuration

### Environment Variables

Create a `.env` file (not included in repo):

```env
LEANIX_URL=https://your-instance.leanix.net
LEANIX_API_TOKEN=your-api-token
LEANIX_WORKSPACE_ID=your-workspace-uuid
```

### LeanIX API Token

1. Log in to LeanIX
2. Go to Admin → API Tokens
3. Create new token with "Survey Management" permissions
4. Copy token (shown only once)

## API Reference

### FastAPI Endpoints

**POST /api/validate**
- Validates survey JSON without creating
- Returns validation status and details

**POST /api/surveys/create**
- Creates survey in LeanIX
- Returns poll ID on success

**GET /api/surveys/{poll_id}**
- Retrieves existing survey
- Returns poll definition

**GET /health**
- Health check endpoint

## Development

### Generate JSON Schema

```bash
python generate_schema.py
```

Outputs `survey_input_schema.json` for use in documentation or external validators.

### Run Tests

```bash
pytest
```

### Code Formatting

```bash
# Format code
black .

# Lint
ruff check .
```

## Troubleshooting

### Validation Errors

**"Questions of type singlechoice must have options"**
- Ensure choice questions include an `options` array

**"Workspace ID must be a valid UUID"**
- Check workspace ID format (e.g., `123e4567-e89b-12d3-a456-426614174000`)

### API Errors

**403 Forbidden**
- Check API token permissions
- Verify workspace ID is correct
- Ensure user has survey creation rights

**422 Unprocessable Entity**
- Review LeanIX-specific field requirements
- Check fact sheet type exists in workspace

## Examples

See the `example_*.json` files for:

1. **example_survey_simple.json** - Minimal survey with 2 questions
2. **example_survey_comprehensive.json** - Full-featured survey with all question types
3. **example_survey_factsheet_mapping.json** - Questions that update fact sheet fields directly

## API Version

This tool uses **LeanIX Poll API v2.0.0**

Endpoint: `/services/poll/v2`

## License

MIT License

## Support

For issues or questions:
1. Check the examples in this repository
2. Review LeanIX API documentation
3. Contact your LeanIX administrator

## Changelog

### v1.0.0 (2024)
- Initial release
- Pydantic models for all question types
- Streamlit UI
- FastAPI backend
- Comprehensive validation
- Example surveys
