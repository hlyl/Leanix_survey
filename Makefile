.PHONY: help install install-dev clean test test-integration lint format run-ui run-api validate-examples

# Default target
help:
	@echo "LeanIX Survey Creator - Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install          Install project dependencies"
	@echo "  make install-dev      Install with dev dependencies"
	@echo ""
	@echo "Run:"
	@echo "  make run-ui           Run Streamlit UI"
	@echo "  make run-api          Run FastAPI backend"
	@echo ""
	@echo "Development:"
	@echo "  make test             Run unit tests"
	@echo "  make test-integration Run integration tests"
	@echo "  make lint             Run linter (ruff)"
	@echo "  make format           Format code (black)"
	@echo "  make type-check       Run type checker (mypy)"
	@echo "  make validate-examples Validate all example files"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean            Remove build artifacts"
	@echo "  make clean-all        Remove build artifacts and venv"

# Setup commands
install:
	uv pip install -e .

install-dev:
	uv pip install -e ".[dev]"

# Run commands
run-ui:
	streamlit run src/streamlit_app.py

run-api:
	uvicorn src.api:app --reload --host 0.0.0.0 --port 8000

# Development commands
test:
	pytest test_models.py -v

test-integration:
	pytest tests/integration/ -v

lint:
	ruff check .

format:
	black .

type-check:
	mypy leanix_survey_models.py api.py validate_survey.py

validate-examples:
	@echo "Validating example survey files..."
	@python -m src.validate_survey examples/example_survey_simple.json
	@python -m src.validate_survey examples/example_survey_comprehensive.json
	@python -m src.validate_survey examples/example_survey_factsheet_mapping.json
	@echo "All examples validated successfully!"

# Cleanup commands
clean:
	rm -rf __pycache__
	rm -rf .pytest_cache
	rm -rf .ruff_cache
	rm -rf .mypy_cache
	rm -rf *.egg-info
	rm -rf build
	rm -rf dist
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

clean-all: clean
	rm -rf .venv
	rm -rf survey_input_schema.json

# Schema generation
schema:
	python generate_schema.py
