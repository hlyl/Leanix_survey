# Project Structure

```
leanix-survey-creator/
├── src/                              # Source code
│   ├── __init__.py
│   ├── leanix_survey_models.py      # Pydantic models and schemas
│   ├── leanix_client.py             # Shared HTTP client
│   ├── leanix_config.py             # Configuration helpers
│   ├── api.py                       # FastAPI backend
│   ├── streamlit_app.py             # Streamlit UI
│   ├── validate_survey.py           # Validation utilities
│   └── generate_schema.py           # JSON Schema generator
│
├── tests/                            # Test suite
│   ├── __init__.py
│   ├── test_models.py               # Unit tests (21 tests)
│   └── integration/                 # Integration tests (15 tests)
│       ├── __init__.py
│       └── test_api_integration.py
│
├── examples/                         # Example survey files
│   ├── example_survey_simple.json
│   ├── example_survey_comprehensive.json
│   ├── example_survey_factsheet_mapping.json
│   └── survey_input_schema.json
│
├── scripts/                          # Utility scripts
│   └── verify_installation.py
│
├── docs/                             # Documentation
│   ├── README.md                    # Getting started
│   ├── RELEASE_NOTES.md             # v1.1.0 release notes
│   ├── API_DOCUMENTATION.md         # API endpoint reference
│   ├── FEATURES.md                  # Feature descriptions
│   ├── ENVIRONMENT_VARIABLES.md     # Environment configuration
│   ├── DEPLOYMENT.md                # Deployment guide
│   ├── SECURITY.md                  # Security best practices
│   └── UV_SETUP.md                  # UV environment setup
│
├── pyproject.toml                   # Project metadata and dependencies
├── Makefile                         # Development commands
├── README.md                        # Main project readme (symlink to docs/)
├── requirements.txt                 # Pinned dependencies (legacy)
├── .python-version                  # Python version (3.12)
├── .gitignore                       # Git ignore rules
└── uv.lock                          # UV lock file

```

## Directory Purposes

### `/src`
Contains all source code organized by functionality:
- **Models**: `leanix_survey_models.py` - Pydantic data models
- **API Client**: `leanix_client.py`, `leanix_config.py` - Shared HTTP client and config
- **Applications**: `api.py`, `streamlit_app.py` - Main applications
- **Utilities**: `validate_survey.py`, `generate_schema.py` - Helper functions

### `/tests`
Comprehensive test suite:
- **Unit Tests**: `test_models.py` (21 tests for data models)
- **Integration Tests**: `tests/integration/test_api_integration.py` (15 tests for API endpoints)

### `/examples`
Sample survey definitions and generated schemas:
- Simple, comprehensive, and fact sheet mapping examples
- Generated JSON schema for validation

### `/scripts`
Standalone utility scripts:
- Installation verification
- Can be run independently

### `/docs`
Complete documentation:
- API reference
- Feature descriptions
- Configuration guide
- Deployment instructions
- Security guidelines
- Setup instructions

## Key Files

### Configuration
- `pyproject.toml` - Project metadata, dependencies, build config
- `Makefile` - Development commands (test, lint, format, run)
- `requirements.txt` - Pinned dependencies for reproducibility

### Documentation
- `README.md` - Main project documentation
- `docs/RELEASE_NOTES.md` - v1.1.0 feature summary

### Environment
- `.python-version` - Python 3.12 specification
- `uv.lock` - Locked dependencies for UV

## Running the Project

```bash
# Install
uv pip install -e .

# Backend API
make run-api
# Available at http://localhost:8000

# Frontend UI
make run-ui
# Available at http://localhost:8501

# Tests
make test                  # Unit tests
make test-integration      # Integration tests

# Development
make lint                  # Ruff linter
make format                # Black formatter
make type-check            # MyPy type checking
```

## Development Workflow

1. **Modify source** in `/src`
2. **Write tests** in `/tests`
3. **Run tests**: `make test`
4. **Format code**: `make format`
5. **Check linting**: `make lint`
6. **Update docs** in `/docs`

## Import Paths

After the reorganization, update imports:

```python
# Old
from leanix_survey_models import SurveyInput
from api import app

# New
from src.leanix_survey_models import SurveyInput
from src.api import app
```

## Building for Distribution

```bash
# Generate distribution
python -m build

# Install from wheel
pip install dist/leanix-survey-creator-1.1.0-py3-none-any.whl
```
