"""
LeanIX configuration helpers and validation utilities.
"""

from __future__ import annotations

from urllib.parse import urlparse
from uuid import UUID

from pydantic import BaseModel, Field


def validate_leanix_url(url: str) -> tuple[bool, list[str]]:
    """Validate LeanIX instance URL.

    Returns tuple of validity and collected error messages.
    """
    errors: list[str] = []
    try:
        result = urlparse(url)
        if not result.scheme or result.scheme not in ["http", "https"]:
            errors.append("URL must use http or https")
        if not result.netloc:
            errors.append("Invalid URL format")
        if url.endswith("/"):
            errors.append("URL should not end with a slash")
    except Exception:
        errors.append("Invalid URL format")
    return len(errors) == 0, errors


def validate_api_token(token: str) -> tuple[bool, list[str]]:
    """Validate LeanIX API token format."""
    errors: list[str] = []
    if not token or len(token.strip()) == 0:
        errors.append("API token cannot be empty")
    elif len(token) < 10:
        errors.append("API token appears too short")
    return len(errors) == 0, errors


class LeanIXConfig(BaseModel):
    """LeanIX API configuration."""

    base_url: str = Field(
        ..., description="LeanIX instance URL (e.g., https://your-instance.leanix.net)"
    )
    api_token: str = Field(..., description="LeanIX API token")
    workspace_id: UUID = Field(..., description="Workspace UUID")

    def validate_config(self) -> tuple[bool, list[str]]:
        """Validate configuration values."""
        errors: list[str] = []
        url_valid, url_errors = validate_leanix_url(self.base_url)
        errors.extend(url_errors)

        _, token_errors = validate_api_token(self.api_token)
        errors.extend(token_errors)

        return len(errors) == 0, errors
