"""
Shared LeanIX API client built on top of a pooled httpx.AsyncClient.
"""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

import httpx
from fastapi import HTTPException, status

from src.leanix_config import LeanIXConfig
from src.leanix_survey_models import PollCreate

logger = logging.getLogger(__name__)


class LeanIXClient:
    """Client for interacting with the LeanIX Poll API."""

    def __init__(self, config: LeanIXConfig, http_client: httpx.AsyncClient):
        if http_client is None:
            raise ValueError("http_client must be provided")
        self.config = config
        self.base_url = config.base_url.rstrip("/")
        self.http_client = http_client
        self.headers = {
            "Authorization": f"Bearer {config.api_token}",
            "Content-Type": "application/json",
        }

    async def create_poll(self, poll_data: PollCreate) -> dict[str, Any]:
        """Create a poll in LeanIX."""
        url = f"{self.base_url}/services/poll/v2/polls"
        params = {"workspaceId": str(self.config.workspace_id)}
        payload = poll_data.model_dump(by_alias=True, exclude_none=True)

        try:
            response = await self.http_client.post(
                url, params=params, headers=self.headers, json=payload
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            error_detail = exc.response.text
            logger.error("LeanIX API error during create_poll: %s", error_detail)
            raise HTTPException(
                status_code=exc.response.status_code,
                detail=f"LeanIX API error: {error_detail}",
            ) from exc
        except httpx.RequestError as exc:
            logger.error("Failed to reach LeanIX during create_poll: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Failed to connect to LeanIX: {exc}",
            ) from exc

    async def get_poll(self, poll_id: UUID) -> dict[str, Any]:
        """Retrieve a poll by ID from LeanIX."""
        url = f"{self.base_url}/services/poll/v2/polls/{poll_id}"
        params = {"workspaceId": str(self.config.workspace_id)}

        try:
            response = await self.http_client.get(url, params=params, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            logger.warning(
                "LeanIX API returned status %s for poll %s", exc.response.status_code, poll_id
            )
            raise HTTPException(
                status_code=exc.response.status_code,
                detail="Poll not found or access denied",
            ) from exc
        except httpx.RequestError as exc:
            logger.error("Failed to reach LeanIX during get_poll: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Failed to connect to LeanIX: {exc}",
            ) from exc
