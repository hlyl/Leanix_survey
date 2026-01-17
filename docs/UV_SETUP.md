# UV Environment Management Setup

This project is configured to use **UV** for fast, modern Python environment management.

## Prerequisites

Install UV if you haven't already:

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or via pip
pip install uv
```

## Quick Start with UV

### 1. Create Virtual Environment

```bash
# UV will automatically use Python 3.12 (from .python-version)
uv venv
```

This creates a `.venv` directory with an isolated Python environment.

### 2. Activate Environment

```bash
# macOS/Linux
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

### 3. Install Dependencies

```bash
# Install all project dependencies
uv pip install -e .

# Or install with dev dependencies
uv pip install -e ".[dev]"
```

The `-e` flag installs in "editable" mode, so changes to the code are immediately available.

## UV Commands Cheat Sheet

### Basic Operations

```bash
# Create virtual environment
uv venv

# Install from pyproject.toml
uv pip install -e .

# Install specific package
uv pip install package-name

# Install from requirements.txt (legacy)
uv pip install -r requirements.txt

# Sync environment (install/upgrade/remove to match pyproject.toml)
uv pip sync
```

### Development Workflow

```bash
# Install with dev dependencies
uv pip install -e ".[dev]"

# Run tests
pytest

# Format code
black .

# Lint code
ruff check .

# Type check
mypy .
```

### Running Applications

```bash
# Streamlit UI
streamlit run streamlit_app.py

# FastAPI backend
uvicorn api:app --reload

# Validate survey
python validate_survey.py example_survey_simple.json
```

## Why UV?

UV is **10-100x faster** than pip/pip-tools:

- ⚡ **Fast**: Written in Rust, resolves dependencies in parallel
- 🔒 **Reliable**: Uses same dependency resolver as pip
- 🎯 **Modern**: Designed for modern Python workflows
- 📦 **Compatible**: Works with existing requirements.txt and pyproject.toml

## Project Structure with UV

```
leanix-survey-creator/
├── .python-version          # Python version (3.12)
├── pyproject.toml           # Project metadata and dependencies
├── .venv/                   # Virtual environment (created by UV)
├── leanix_survey_models.py  # Source code
├── streamlit_app.py
├── api.py
└── ...
```

## Dependency Management

### Adding New Dependencies

```bash
# Add to pyproject.toml manually, then:
uv pip install -e .

# Or install directly (manual pyproject.toml update needed)
uv pip install new-package
```

### Updating Dependencies

```bash
# Update all packages
uv pip install --upgrade -e .

# Update specific package
uv pip install --upgrade package-name
```

### Lock Dependencies (Recommended for Production)

```bash
# Generate requirements.txt from current environment
uv pip freeze > requirements-lock.txt

# Install from locked requirements
uv pip install -r requirements-lock.txt
```

## Environment Variables

Create a `.env` file for configuration:

```bash
# .env
LEANIX_URL=https://your-instance.leanix.net
LEANIX_API_TOKEN=your-token-here
LEANIX_WORKSPACE_ID=your-workspace-uuid
```

Then load in Python:

```python
from dotenv import load_dotenv
import os

load_dotenv()
leanix_url = os.getenv("LEANIX_URL")
```

## Common Issues

### "Command not found: uv"

UV is not in your PATH. Reinstall or add to PATH:

```bash
# Add to ~/.bashrc or ~/.zshrc
export PATH="$HOME/.cargo/bin:$PATH"
```

### "Python 3.12 not found"

Install Python 3.12 or update `.python-version` to your version:

```bash
# Check your Python version
python --version

# Update .python-version if needed
echo "3.11" > .python-version  # or your version
```

### Virtual Environment Issues

```bash
# Remove and recreate
rm -rf .venv
uv venv
source .venv/bin/activate
uv pip install -e .
```

## Migration from pip

If you have an existing `requirements.txt`:

```bash
# One-time migration
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt

# Then switch to pyproject.toml
uv pip install -e .
```

## Best Practices

1. **Always activate** the virtual environment before working
2. **Use pyproject.toml** for dependency management
3. **Commit** `.python-version` and `pyproject.toml` to git
4. **Don't commit** `.venv/` directory (add to `.gitignore`)
5. **Lock dependencies** for reproducible builds

## Additional Resources

- UV Documentation: https://github.com/astral-sh/uv
- pyproject.toml Guide: https://packaging.python.org/guides/writing-pyproject-toml/
- Python Packaging: https://packaging.python.org/
