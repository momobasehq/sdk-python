from __future__ import annotations

from typing import Any

import httpx


class MomobaseAPIError(Exception):
    """A non-successful Momobase API response: HTTP `status`, stable Momobase `code`,
    and the parsed `body` when available."""

    def __init__(self, status: int, code: str, message: str, body: Any) -> None:
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message
        self.body = body

    @classmethod
    def from_response(cls, response: httpx.Response) -> MomobaseAPIError:
        """Parses an API error from an HTTP response."""
        try:
            body: Any = response.json()
        except ValueError:
            body = response.text
        envelope = body if isinstance(body, dict) else {}
        # OAuth endpoints may answer with a bare string, e.g. {"error": "invalid_grant"}.
        error = envelope.get("error")
        error = error if isinstance(error, dict) else {}
        return cls(
            response.status_code,
            error.get("code") or f"HTTP_{response.status_code}",
            error.get("message") or envelope.get("message") or response.reason_phrase,
            body,
        )
