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
        self._access_token: str | None = None
        self._token_expiry: float = 0

    async def _get_access_token(self) -> str:
        """Exchange API token for OAuth access token if needed."""
        import time

        # Check if we have a valid cached token
        if self._access_token and time.time() < self._token_expiry:
            return self._access_token

        # Exchange API token for access token
        oauth_url = f"{self.base_url}/services/mtm/v1/oauth2/token"
        auth = ("apitoken", self.config.api_token)

        try:
            response = await self.http_client.post(
                oauth_url,
                auth=auth,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data={"grant_type": "client_credentials"},
            )
            response.raise_for_status()
            token_data = response.json()
            self._access_token = token_data["access_token"]
            # Cache token with 60 second buffer before expiry
            self._token_expiry = time.time() + token_data.get("expires_in", 3600) - 60
            return self._access_token
        except Exception as exc:
            logger.error("Failed to exchange API token for access token: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to authenticate with LeanIX",
            ) from exc

    async def _get_headers(self) -> dict[str, str]:
        """Get headers with valid access token."""
        access_token = await self._get_access_token()
        return {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

    async def create_poll(self, poll_data: PollCreate) -> dict[str, Any]:
        """Create a poll in LeanIX."""
        url = f"{self.base_url}/services/poll/v2/polls"
        params = {"workspaceId": str(self.config.workspace_id)}
        payload = poll_data.model_dump(by_alias=True, exclude_none=True)
        headers = await self._get_headers()

        logger.debug(f"Creating poll at {url}")
        logger.debug(f"Payload: {payload}")

        try:
            response = await self.http_client.post(
                url, params=params, headers=headers, json=payload
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
        headers = await self._get_headers()

        try:
            response = await self.http_client.get(url, params=params, headers=headers)
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
