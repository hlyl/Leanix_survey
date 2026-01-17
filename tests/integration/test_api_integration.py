"""
Integration tests for API endpoints.

Tests cover:
- Validation endpoint
- Single survey creation
- Batch survey creation with fail-fast
- Poll retrieval with optional caching
- Shared HTTP client lifecycle
"""

from __future__ import annotations

import json
from unittest.mock import patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from src.api import (
    MAX_BATCH_SIZE,
    app,
)


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def valid_survey_json():
    """Valid survey JSON for testing."""
    return json.dumps(
        {
            "title": "Test Survey",
            "questionnaire": {
                "questions": [
                    {
                        "id": "q1",
                        "label": "Test Question",
                        "type": "text",
                    }
                ]
            },
            "userQuery": {"roles": [{"subscriptionType": "RESPONSIBLE"}]},
        }
    )


@pytest.fixture
def valid_survey_dict():
    """Valid survey dict for testing."""
    return {
        "title": "Test Survey",
        "questionnaire": {
            "questions": [
                {
                    "id": "q1",
                    "label": "Test Question",
                    "type": "text",
                }
            ]
        },
        "userQuery": {"roles": [{"subscriptionType": "RESPONSIBLE"}]},
    }


@pytest.fixture
def leanix_credentials():
    """LeanIX credentials for testing."""
    return {
        "leanix_url": "https://example.leanix.net",
        "api_token": "test-token-1234567890",
        "workspace_id": str(uuid4()),
    }


class TestValidationEndpoint:
    """Tests for the /api/validate endpoint."""

    def test_validate_valid_survey(self, client, valid_survey_json):
        """Test validation of a valid survey."""
        response = client.post("/api/validate", json={"json_input": valid_survey_json})
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["message"] == "Survey definition is valid"
        assert data["survey_input"] is not None
        assert data["survey_input"]["title"] == "Test Survey"
        assert data["details"]["question_count"] == 1

    def test_validate_invalid_json(self, client):
        """Test validation with invalid JSON."""
        response = client.post("/api/validate", json={"json_input": "not valid json"})
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert data["error"] is not None

    def test_validate_missing_required_field(self, client):
        """Test validation with missing required field."""
        invalid_json = json.dumps(
            {
                "questionnaire": {
                    "questions": [{"id": "q1", "label": "Q1", "type": "text"}]
                }
            }
        )
        response = client.post("/api/validate", json={"json_input": invalid_json})
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False

    def test_validate_choice_without_options(self, client):
        """Test validation of choice question without options."""
        invalid_json = json.dumps(
            {
                "title": "Test",
                "questionnaire": {
                    "questions": [{"id": "q1", "label": "Q1", "type": "singlechoice"}]
                },
                "userQuery": {"roles": [{"subscriptionType": "RESPONSIBLE"}]},
            }
        )
        response = client.post("/api/validate", json={"json_input": invalid_json})
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False


class TestCreateSurveyEndpoint:
    """Tests for the /api/surveys/create endpoint."""

    @pytest.mark.asyncio
    async def test_create_survey_success(self, client, valid_survey_dict, leanix_credentials):
        """Test successful survey creation with mocked LeanIX response."""
        with patch("src.leanix_client.LeanIXClient.create_poll") as mock_create:
            mock_create.return_value = {
                "status": "OK",
                "data": {"id": "poll-123"},
            }

            response = client.post(
                "/api/surveys/create",
                params=leanix_credentials,
                json={
                    "survey_input": valid_survey_dict,
                    "language": "en",
                    "fact_sheet_type": "Application",
                    "due_date": None,
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["poll_id"] == "poll-123"
        assert data["message"] == "Survey created successfully in LeanIX"

    @pytest.mark.asyncio
    async def test_create_survey_invalid_config(self, client, valid_survey_dict):
        """Test survey creation with invalid LeanIX config."""
        response = client.post(
            "/api/surveys/create",
            params={
                "leanix_url": "not-a-url",
                "api_token": "token",
                "workspace_id": str(uuid4()),  # Valid UUID but invalid URL
            },
            json={
                "survey_input": valid_survey_dict,
                "language": "en",
                "fact_sheet_type": "Application",
            },
        )

        assert response.status_code == 422
        data = response.json()
        assert "Invalid configuration" in data["detail"]


class TestBatchCreateSurveyEndpoint:
    """Tests for the /api/surveys/create-batch endpoint."""

    @pytest.mark.asyncio
    async def test_batch_create_single_item(self, client, valid_survey_dict, leanix_credentials):
        """Test batch creation with single survey."""
        with patch("src.leanix_client.LeanIXClient.create_poll") as mock_create:
            mock_create.return_value = {
                "status": "OK",
                "data": {"id": "poll-1"},
            }

            batch_payload = {
                "requests": [
                    {
                        "survey_input": valid_survey_dict,
                        "language": "en",
                        "fact_sheet_type": "Application",
                        "due_date": None,
                    }
                ],
                "fail_fast": True,
            }

            response = client.post(
                "/api/surveys/create-batch",
                params=leanix_credentials,
                json=batch_payload,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["succeeded"] == 1
        assert data["failed"] == 0
        assert len(data["results"]) == 1
        assert data["results"][0]["poll_id"] == "poll-1"

    @pytest.mark.asyncio
    async def test_batch_create_multiple_items(
        self, client, valid_survey_dict, leanix_credentials
    ):
        """Test batch creation with multiple surveys."""
        with patch("src.leanix_client.LeanIXClient.create_poll") as mock_create:
            mock_create.return_value = {
                "status": "OK",
                "data": {"id": "poll-x"},
            }

            batch_payload = {
                "requests": [
                    {
                        "survey_input": valid_survey_dict,
                        "language": "en",
                        "fact_sheet_type": "Application",
                        "due_date": None,
                    }
                    for _ in range(3)
                ],
                "fail_fast": False,
            }

            response = client.post(
                "/api/surveys/create-batch",
                params=leanix_credentials,
                json=batch_payload,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["succeeded"] == 3
        assert data["failed"] == 0
        assert len(data["results"]) == 3

    def test_batch_create_exceeds_max_size(self, client, valid_survey_dict, leanix_credentials):
        """Test batch creation exceeding max batch size."""
        batch_payload = {
            "requests": [
                {
                    "survey_input": valid_survey_dict,
                    "language": "en",
                    "fact_sheet_type": "Application",
                    "due_date": None,
                }
                for _ in range(MAX_BATCH_SIZE + 1)
            ],
            "fail_fast": False,
        }

        response = client.post(
            "/api/surveys/create-batch",
            params=leanix_credentials,
            json=batch_payload,
        )

        assert response.status_code == 422
        data = response.json()
        assert "exceeds maximum" in data["detail"]

    def test_batch_create_empty(self, client, leanix_credentials):
        """Test batch creation with empty requests."""
        batch_payload = {"requests": [], "fail_fast": True}

        response = client.post(
            "/api/surveys/create-batch",
            params=leanix_credentials,
            json=batch_payload,
        )

        assert response.status_code == 400
        data = response.json()
        assert "cannot be empty" in data["detail"]

    @pytest.mark.asyncio
    async def test_batch_create_fail_fast_on_error(
        self, client, valid_survey_dict, leanix_credentials
    ):
        """Test batch creation with fail-fast enabled stops on first error."""
        with patch("src.leanix_client.LeanIXClient.create_poll") as mock_create:

            def side_effect(*args, **kwargs):
                from fastapi import HTTPException

                raise HTTPException(status_code=400, detail="Test error")

            mock_create.side_effect = side_effect

            batch_payload = {
                "requests": [
                    {
                        "survey_input": valid_survey_dict,
                        "language": "en",
                        "fact_sheet_type": "Application",
                        "due_date": None,
                    }
                    for _ in range(3)
                ],
                "fail_fast": True,
            }

            response = client.post(
                "/api/surveys/create-batch",
                params=leanix_credentials,
                json=batch_payload,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        # With fail_fast, should stop after first error (so 1 result)
        assert len(data["results"]) == 1
        assert data["results"][0]["success"] is False


class TestGetSurveyEndpoint:
    """Tests for the /api/surveys/{poll_id} endpoint."""

    @pytest.mark.asyncio
    async def test_get_survey_success(self, client, leanix_credentials):
        """Test successful poll retrieval."""
        poll_id = uuid4()
        with patch("src.leanix_client.LeanIXClient.get_poll") as mock_get:
            mock_get.return_value = {
                "status": "OK",
                "data": {"id": str(poll_id), "title": "Retrieved Poll"},
            }

            response = client.get(
                f"/api/surveys/{poll_id}",
                params=leanix_credentials,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["id"] == str(poll_id)

    @pytest.mark.asyncio
    async def test_get_survey_not_found(self, client, leanix_credentials):
        """Test poll retrieval when poll does not exist."""
        poll_id = uuid4()
        with patch("src.leanix_client.LeanIXClient.get_poll") as mock_get:
            from fastapi import HTTPException

            mock_get.side_effect = HTTPException(status_code=404, detail="Not found")

            response = client.get(
                f"/api/surveys/{poll_id}",
                params=leanix_credentials,
            )

        assert response.status_code == 404


class TestHealthEndpoint:
    """Tests for the /health endpoint."""

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestRootEndpoint:
    """Tests for the root endpoint."""

    def test_root_endpoint(self, client):
        """Test root endpoint returns API info."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "LeanIX Survey Creator"
        assert data["version"] == "1.0.0"
