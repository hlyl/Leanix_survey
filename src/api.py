"""
FastAPI application for creating LeanIX surveys programmatically.

This service provides endpoints to:
1. Validate survey JSON definitions
2. Create polls in LeanIX (single or batch)
3. Retrieve polls with optional caching
"""

from __future__ import annotations

import asyncio
import logging
import os
from datetime import date
from typing import Any
from uuid import UUID

import httpx
from cachetools import TTLCache
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.leanix_client import LeanIXClient
from src.leanix_config import LeanIXConfig
from src.leanix_survey_models import PollCreate, SurveyInput

# Configure logging
logging.basicConfig(
    level=logging.getLevelName(os.getenv("LOG_LEVEL", "INFO")),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


app = FastAPI(
    title="LeanIX Survey Creator",
    description="API for validating and creating LeanIX surveys programmatically",
    version="1.0.0",
)

# CORS middleware - restricted to specified origins for security
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8501").split(
    ","
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)

logger.info(f"Allowed CORS origins: {', '.join(allowed_origins)}")
logger.info(f"Allowed CORS origins: {', '.join(allowed_origins)}")


# ============================================================================
# Runtime Configuration
# ============================================================================

API_TIMEOUT = float(os.getenv("API_TIMEOUT", "30"))
MAX_CONNECTIONS = int(os.getenv("MAX_CONNECTIONS", "10"))
MAX_KEEPALIVE_CONNECTIONS = int(os.getenv("MAX_KEEPALIVE_CONNECTIONS", "5"))
MAX_BATCH_SIZE = int(os.getenv("MAX_BATCH_SIZE", "25"))
CACHE_ENABLED = os.getenv("CACHE_ENABLED", "false").lower() == "true"
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "300"))
CACHE_MAX_ITEMS = int(os.getenv("CACHE_MAX_ITEMS", "128"))


class PollCache:
    """Thread-safe TTL cache wrapper for poll responses."""

    def __init__(self, ttl_seconds: int, max_items: int):
        self._cache = TTLCache(maxsize=max_items, ttl=ttl_seconds)
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Any | None:
        async with self._lock:
            return self._cache.get(key)

    async def set(self, key: str, value: Any) -> None:
        async with self._lock:
            self._cache[key] = value


def build_http_client() -> httpx.AsyncClient:
    """Create a shared AsyncClient with pooling and timeouts."""
    limits = httpx.Limits(
        max_connections=MAX_CONNECTIONS,
        max_keepalive_connections=MAX_KEEPALIVE_CONNECTIONS,
    )
    transport = httpx.AsyncHTTPTransport(retries=3)
    return httpx.AsyncClient(timeout=API_TIMEOUT, limits=limits, transport=transport)


class ValidateRequest(BaseModel):
    """Request to validate survey JSON string."""

    json_input: str = Field(..., description="Raw JSON string to validate")


class ValidateResponse(BaseModel):
    """Response from survey validation."""

    valid: bool
    message: str
    survey_input: dict[str, Any] | None = None
    error: str | None = None
    details: dict[str, Any] | None = None


class SurveyCreateRequest(BaseModel):
    """Request to create a survey in LeanIX"""

    survey_input: SurveyInput = Field(..., description="Survey definition")
    language: str = Field("en", description="Survey language code")
    fact_sheet_type: str = Field(..., description="Fact sheet type to survey")
    due_date: date | None = Field(None, description="Survey due date")


class SurveyCreateResponse(BaseModel):
    """Response after creating a survey"""

    success: bool
    poll_id: str | None = None
    message: str
    errors: list[str] | None = None


class BatchSurveyItemResult(BaseModel):
    """Result for a single survey creation in a batch request."""

    index: int
    success: bool
    poll_id: str | None = None
    message: str
    errors: list[str] | None = None


class BatchSurveyCreateRequest(BaseModel):
    """Batch request to create multiple surveys."""

    requests: list[SurveyCreateRequest]
    fail_fast: bool = Field(True, description="Stop processing after the first failure when true")


class BatchSurveyCreateResponse(BaseModel):
    """Batch response summarizing per-item outcomes."""

    success: bool
    succeeded: int
    failed: int
    results: list[BatchSurveyItemResult]
    message: str


# ============================================================================
# LeanIX API Client helpers
# ============================================================================


def get_http_client(request: Request) -> httpx.AsyncClient:
    """Return the shared AsyncClient stored on the app state."""
    http_client = getattr(request.app.state, "http_client", None)
    if http_client is None:
        http_client = build_http_client()
        request.app.state.http_client = http_client
    return http_client


def get_poll_cache(request: Request) -> PollCache | None:
    """Return the poll cache if caching is enabled."""
    return getattr(request.app.state, "poll_cache", None)


def make_cache_key(workspace_id: UUID, poll_id: UUID) -> str:
    return f"{workspace_id}:{poll_id}"


# ============================================================================
# API Endpoints
# ============================================================================


@app.get("/")
async def root() -> dict:
    """Root endpoint with API information"""
    logger.info("Root endpoint accessed")
    return {
        "service": "LeanIX Survey Creator",
        "version": "1.0.0",
        "endpoints": {"validate": "/api/validate", "create": "/api/surveys/create"},
    }


@app.post("/api/validate", response_model=ValidateResponse)
async def validate_survey(req: ValidateRequest) -> ValidateResponse:
    """
    Validate a survey definition without creating it.

    Accepts raw JSON string and validates it against the SurveyInput schema.
    """
    import json

    logger.info("Validating survey JSON")
    try:
        # Parse raw JSON
        parsed_data = json.loads(req.json_input)

        # Validate against SurveyInput model
        survey_input = SurveyInput(**parsed_data)
        logger.info(f"Survey validation passed: {survey_input.title}")

        return ValidateResponse(
            valid=True,
            message="Survey definition is valid",
            survey_input=survey_input.model_dump(by_alias=True),
            details={
                "title": survey_input.title,
                "question_count": len(survey_input.questionnaire.questions),
                "has_user_query": survey_input.user_query is not None,
                "has_fact_sheet_query": survey_input.fact_sheet_query is not None,
            },
        )
    except json.JSONDecodeError as exc:
        error_msg = f"Invalid JSON: {exc}"
        logger.warning(error_msg)
        return ValidateResponse(valid=False, message="Invalid JSON", error=error_msg)
    except Exception as exc:
        error_msg = str(exc)
        logger.warning(f"Validation error: {error_msg}")
        return ValidateResponse(valid=False, message="Validation failed", error=error_msg)


@app.post("/api/surveys/create", response_model=SurveyCreateResponse)
async def create_survey(
    create_request: SurveyCreateRequest,
    request: Request,
    leanix_url: str = Query(..., description="LeanIX instance URL"),
    api_token: str = Query(..., description="LeanIX API token"),
    workspace_id: UUID = Query(..., description="Workspace UUID"),
) -> SurveyCreateResponse:
    """
    Create a survey in LeanIX.

    This endpoint:
    1. Validates the survey definition
    2. Combines it with UI-provided metadata (language, fact sheet type, due date)
    3. Creates the poll in LeanIX via API

    Returns the created poll ID and status.
    """
    logger.info(f"Creating survey: {create_request.survey_input.title}")

    try:
        # Validate configuration
        config = LeanIXConfig(base_url=leanix_url, api_token=api_token, workspace_id=workspace_id)
        is_valid, errors = config.validate_config()
        if not is_valid:
            logger.warning(f"Invalid LeanIX configuration: {errors}")
            raise HTTPException(status_code=422, detail=f"Invalid configuration: {errors}")

        http_client = get_http_client(request)
        client = LeanIXClient(config, http_client)

        # Build poll creation request
        poll_data = PollCreate.from_survey_input(
            survey_input=create_request.survey_input,
            language=create_request.language,
            fact_sheet_type=create_request.fact_sheet_type,
            due_date=create_request.due_date,
            transform_ids_to_uuid=True,
        )

        # Debug logging
        logger.debug(f"Poll data prepared: {poll_data.model_dump(by_alias=True, exclude_none=True)}")

        # Create poll in LeanIX
        logger.info("Sending poll creation request to LeanIX")
        response = await client.create_poll(poll_data)

        # Extract poll ID from response
        poll_id = None
        if response.get("status") == "OK" and response.get("data"):
            poll_id = response["data"].get("id")
            logger.info(f"Survey created successfully with poll ID: {poll_id}")

        return SurveyCreateResponse(
            success=True, poll_id=poll_id, message="Survey created successfully in LeanIX"
        )

    except HTTPException:
        logger.error("HTTP error creating survey", exc_info=True)
        raise

    except Exception as e:
        logger.error(f"Failed to create survey: {str(e)}", exc_info=True)
        return SurveyCreateResponse(
            success=False, message=f"Failed to create survey: {str(e)}", errors=[str(e)]
        )


@app.post("/api/surveys/create-batch", response_model=BatchSurveyCreateResponse)
async def create_survey_batch(
    batch_request: BatchSurveyCreateRequest,
    request: Request,
    leanix_url: str = Query(..., description="LeanIX instance URL"),
    api_token: str = Query(..., description="LeanIX API token"),
    workspace_id: UUID = Query(..., description="Workspace UUID"),
) -> BatchSurveyCreateResponse:
    """Create multiple surveys in LeanIX with optional fail-fast behavior."""

    if not batch_request.requests:
        raise HTTPException(status_code=400, detail="Batch requests cannot be empty")
    if len(batch_request.requests) > MAX_BATCH_SIZE:
        raise HTTPException(
            status_code=422,
            detail=f"Batch size exceeds maximum of {MAX_BATCH_SIZE}",
        )

    logger.info("Processing batch survey creation: %s items", len(batch_request.requests))

    config = LeanIXConfig(base_url=leanix_url, api_token=api_token, workspace_id=workspace_id)
    is_valid, errors = config.validate_config()
    if not is_valid:
        raise HTTPException(status_code=422, detail=f"Invalid configuration: {errors}")

    http_client = get_http_client(request)
    client = LeanIXClient(config, http_client)

    results: list[BatchSurveyItemResult] = []

    for index, create_request in enumerate(batch_request.requests):
        try:
            poll_data = PollCreate.from_survey_input(
                survey_input=create_request.survey_input,
                language=create_request.language,
                fact_sheet_type=create_request.fact_sheet_type,
                due_date=create_request.due_date,
                transform_ids_to_uuid=True,
            )
            response = await client.create_poll(poll_data)

            poll_id = None
            if response.get("status") == "OK" and response.get("data"):
                poll_id = response["data"].get("id")

            results.append(
                BatchSurveyItemResult(
                    index=index,
                    success=True,
                    poll_id=poll_id,
                    message="Survey created successfully",
                )
            )
        except HTTPException as exc:
            error_msg = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
            results.append(
                BatchSurveyItemResult(
                    index=index,
                    success=False,
                    poll_id=None,
                    message="Failed to create survey",
                    errors=[error_msg],
                )
            )
            if batch_request.fail_fast:
                logger.warning("Fail-fast enabled; stopping batch after index %s", index)
                break
        except Exception as exc:  # pragma: no cover - defensive
            results.append(
                BatchSurveyItemResult(
                    index=index,
                    success=False,
                    poll_id=None,
                    message="Unexpected error during survey creation",
                    errors=[str(exc)],
                )
            )
            if batch_request.fail_fast:
                logger.warning(
                    "Fail-fast enabled; stopping batch after unexpected error at %s", index
                )
                break

    succeeded = sum(1 for r in results if r.success)
    failed = sum(1 for r in results if not r.success)
    success = failed == 0
    message = f"Batch completed: {succeeded} succeeded, {failed} failed"

    return BatchSurveyCreateResponse(
        success=success,
        succeeded=succeeded,
        failed=failed,
        results=results,
        message=message,
    )


@app.get("/api/surveys/{poll_id}")
async def get_survey(
    poll_id: UUID,
    request: Request,
    leanix_url: str = Query(..., description="LeanIX instance URL"),
    api_token: str = Query(..., description="LeanIX API token"),
    workspace_id: UUID = Query(..., description="Workspace UUID"),
) -> dict:
    """
    Retrieve a survey from LeanIX.

    Returns the poll definition including all questions and configuration.
    """
    logger.info("Retrieving survey: %s", poll_id)
    config = LeanIXConfig(base_url=leanix_url, api_token=api_token, workspace_id=workspace_id)
    is_valid, errors = config.validate_config()
    if not is_valid:
        raise HTTPException(status_code=422, detail=f"Invalid configuration: {errors}")

    cache = get_poll_cache(request) if CACHE_ENABLED else None
    cache_key = make_cache_key(config.workspace_id, poll_id)

    if cache:
        cached_response = await cache.get(cache_key)
        if cached_response is not None:
            logger.info("Cache hit for poll %s", poll_id)
            return cached_response

    http_client = get_http_client(request)
    client = LeanIXClient(config, http_client)
    response = await client.get_poll(poll_id)

    if cache:
        await cache.set(cache_key, response)

    return response


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


# ============================================================================
# Startup/Shutdown Events
# ============================================================================


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    logger.info("LeanIX Survey Creator API starting up...")
    app.state.http_client = build_http_client()
    if CACHE_ENABLED:
        app.state.poll_cache = PollCache(CACHE_TTL_SECONDS, CACHE_MAX_ITEMS)
        logger.info(
            "Poll cache enabled (ttl=%ss, max_items=%s)", CACHE_TTL_SECONDS, CACHE_MAX_ITEMS
        )


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("LeanIX Survey Creator API shutting down...")
    http_client = getattr(app.state, "http_client", None)
    if http_client:
        await http_client.aclose()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
