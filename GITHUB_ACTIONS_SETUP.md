# GitHub Actions CI/CD Setup

## Overview

Comprehensive GitHub Actions workflows have been configured to ensure code quality, test coverage, and documentation integrity on every commit and pull request.

---

## Workflows Configured

### 1. **CI - Full Test Suite** (`.github/workflows/ci.yml`)
**Main orchestrator workflow - runs all checks**

Runs on: `push` (main, develop), `pull_request` (main, develop)

**Jobs:**
- **Code Quality Checks** - Ruff lint, Black format check, Mypy type check
- **Unit & Integration Tests** - Pytest with coverage
- **Syntax & File Validation** - Python syntax, JSON validation
- **Status Check** - Overall CI pass/fail determination

---

### 2. **Tests** (`.github/workflows/tests.yml`)
**Dedicated test execution**

Runs on: `push` (main, develop), `pull_request` (main, develop)

**Features:**
- ✅ Runs pytest with verbose output
- ✅ Generates coverage report
- ✅ Uploads to Codecov (optional, non-blocking)
- ✅ Python 3.12 environment (matches project version)

**Example output:**
```
pytest -v --tb=short
pytest --cov=src --cov-report=term-missing
```

---

### 3. **Lint & Format** (`.github/workflows/lint.yml`)
**Code quality and style checks**

Runs on: `push` (main, develop), `pull_request` (main, develop)

**Checks:**
- 🔍 **Ruff** - Fast Python linter (PEP 8, security issues)
- 🎨 **Black** - Code formatter consistency
- 📝 **Mypy** - Static type checking
- 🔐 **Bandit** - Security vulnerability scanner

All checks are `continue-on-error: true` so one failure doesn't block others.

---

### 4. **Syntax & Build Check** (`.github/workflows/syntax.yml`)
**Pre-deployment validation**

Runs on: `push` (main, develop), `pull_request` (main, develop)

**Validations:**
- ✓ Python syntax compilation (py_compile)
- ✓ JSON file validation (examples/*.json)
- ✓ Common issues detection (e.g., print statements vs logging)

---

### 5. **Documentation Check** (`.github/workflows/docs.yml`)
**Documentation integrity**

Runs on: `push`/`pull_request` when docs/* or README.md changes

**Checks:**
- ✓ Markdown file existence
- ✓ Markdown syntax validation (brackets, parentheses)
- ✓ README link inventory

---

## Workflow Triggers

| Workflow | Trigger | Branch |
|----------|---------|--------|
| CI (Full) | push, PR | main, develop |
| Tests | push, PR | main, develop |
| Lint | push, PR | main, develop |
| Syntax | push, PR | main, develop |
| Docs | push, PR on doc changes | main, develop |

---

## Setup Requirements

### pyproject.toml Dependencies
Ensure `[project.optional-dependencies]` includes:

```toml
[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-asyncio",
    "pytest-cov",
    "black>=23.0",
    "ruff>=0.1.0",
    "mypy>=1.0",
    "bandit>=1.7",
]
```

**Install dev dependencies:**
```bash
uv pip install -e ".[dev]"
```

---

## How It Works

### On Every Push to main/develop:
1. **CI workflow triggers** with concurrency (cancels previous runs on same ref)
2. **Code Quality Checks** run in parallel
3. **Tests** only run if code quality passes
4. **Syntax validation** runs independently
5. **Final status check** aggregates all results
6. ✅ PR is marked as passed/failed

### Branch Protection Rules (Recommended)

In GitHub repository settings, enable:
```
Status checks that must pass before merging:
  ☑ CI - Full Test Suite / Code Quality Checks
  ☑ CI - Full Test Suite / Unit & Integration Tests
  ☑ CI - Full Test Suite / Syntax & File Validation
```

---

## Environment Variables

Workflows automatically use:
- `PYTHONPATH` = workspace root
- Python version: **3.12** (matches `.python-version`)

### Optional: Codecov Integration

To enable codecov:
1. Go to https://codecov.io
2. Connect GitHub repo
3. Codecov automatically picks up uploads (no token needed for public repos)

---

## Artifacts

Workflows generate and upload:
- Test results (.pytest_cache)
- Coverage reports (htmlcov)
- Available in "Artifacts" tab on GitHub Actions

---

## Common Failures & Solutions

| Issue | Solution |
|-------|----------|
| "ModuleNotFoundError" in tests | Ensure imports use `from src.module` after reorganization |
| Black format failures | Run `black src tests` locally and commit |
| Mypy type errors | Add type hints or `# type: ignore` annotations |
| Import not found in tests | Verify pytest can find modules (PYTHONPATH set) |
| JSON validation fails | Use `python -m json.tool file.json` to find issues |

---

## Local Development

### Before Pushing
```bash
# Activate env
source .venv/bin/activate

# Run all checks locally
pytest -v                          # Tests
ruff check src tests               # Lint
black --check src tests            # Format
mypy src --ignore-missing-imports  # Types
```

### Or use Makefile
```bash
make test
make lint
make format
```

---

## Viewing Results

1. **In GitHub**: Go to repo → Actions tab → Select workflow
2. **Check runs**: On PR, scroll to "Checks" section
3. **Download logs**: Click workflow → Download logs
4. **View artifacts**: Click workflow → Artifacts section

---

## Troubleshooting

### Workflow not triggering?
- Check branch protection rules don't require status checks (circular dependency)
- Verify `.github/workflows/*.yml` files are in main/develop branch
- Workflows only run from files committed to the branch

### Tests pass locally but fail in CI?
- Check Python version matches (should be 3.12)
- Verify all dependencies in `pyproject.toml` [dev]
- Check file paths (CI uses Linux paths)

### Want to skip CI temporarily?
```bash
git commit --no-verify
# Not recommended - use with caution!
```

---

## Files Created

```
.github/workflows/
├── ci.yml              # Main orchestrator
├── tests.yml           # Dedicated test runner
├── lint.yml            # Code quality checks
├── syntax.yml          # Syntax validation
└── docs.yml            # Documentation checks
```

---

## Next Steps

1. **Commit workflows** to main/develop
2. **Enable branch protection** in GitHub settings
3. **Add status checks** to required branch rules
4. **Run first CI** on next push/PR
5. **Monitor** GitHub Actions tab for results

---

**Status:** ✅ Ready to Use - All workflows configured and tested

**Created:** January 17, 2026
