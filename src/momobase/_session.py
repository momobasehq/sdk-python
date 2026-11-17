from __future__ import annotations

import threading
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Self
from urllib.parse import quote

import httpx

from .errors import MomobaseAPIError
from .types import OAuthTokenResponse


@dataclass(frozen=True)
class TokenSnapshot:
    """The current session tokens and the epoch seconds at which they expire."""

    access_token: str
    refresh_token: str | None
    expires_at: float


def _q(segment: str) -> str:
    """Escapes a resource id for use as one path segment."""
    return quote(segment, safe="")


def _encode(value: Any) -> str | None:
    """Renders one list query value as the API expects it, or None to leave it out.

    Sequences become a comma-separated "any of", datetimes ISO 8601 (a naive one is
    read as local time), and booleans lowercase.
    """
    if value is None:
        return None
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, datetime):
        aware = value if value.tzinfo else value.astimezone()
        return aware.isoformat()
    if isinstance(value, Sequence) and not isinstance(value, str):
        joined = ",".join(str(part) for part in value if str(part) != "")
        return joined or None
    return str(value) or None


def _unwrap(response: httpx.Response) -> Any:
    body = response.json() if response.is_success else None
    enveloped = isinstance(body, dict) and "success" in body
    if not response.is_success or (enveloped and not body["success"]):
        raise MomobaseAPIError.from_response(response)
    return body.get("data") if enveloped else body


class _Session:
    """Holds an OAuth session and issues authenticated requests against it."""

    _refresh_path: str

    def __init__(
        self,
        base_url: str,
        token_skew_seconds: float,
        http_client: httpx.Client | None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._skew = token_skew_seconds
        self._http = http_client or httpx.Client(timeout=30)
        self._token: TokenSnapshot | None = None
        self._on_token_change: Callable[[TokenSnapshot | None], None] | None = None
        self._lock = threading.Lock()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def close(self) -> None:
        """Closes the underlying HTTP client."""
        self._http.close()

    def authenticate(self) -> OAuthTokenResponse:
        """Authenticates with the configured credentials and stores the token."""
        raise NotImplementedError

    def refresh(self) -> OAuthTokenResponse:
        """Refreshes the session, falling back to a fresh authentication."""
        token = self._token
        if token is None or not token.refresh_token:
            return self.authenticate()
        try:
            return self._form(
                self._refresh_path,
                {"grant_type": "refresh_token", "refresh_token": token.refresh_token},
            )
        except MomobaseAPIError:
            self.clear_token()
            return self.authenticate()

    def get_token(self) -> TokenSnapshot | None:
        """Returns the current session tokens, or None when there is no session."""
        return self._token

    def clear_token(self) -> None:
        """Clears the active session token."""
        self._token = None
        if self._on_token_change:
            self._on_token_change(None)

    def _set_token(
        self, access_token: str, refresh_token: str | None, expires_in: float | None
    ) -> None:
        # Without a lifetime the token counts as expired, so the next request refreshes.
        ttl = 0 if expires_in is None else max(expires_in - self._skew, 1)
        self._token = TokenSnapshot(access_token, refresh_token, time.time() + ttl)
        if self._on_token_change:
            self._on_token_change(self._token)

    def _form(self, path: str, values: dict[str, str]) -> OAuthTokenResponse:
        response = self._http.post(self._base_url + path, data=values)
        if not response.is_success:
            raise MomobaseAPIError.from_response(response)
        token: OAuthTokenResponse = response.json()
        self._set_token(
            token["access_token"], token.get("refresh_token"), token["expires_in"]
        )
        return token

    def _bearer(self, stale: TokenSnapshot | None = None) -> TokenSnapshot:
        token = self._token
        if token is None or token is stale or token.expires_at <= time.time():
            with self._lock:
                # Threads that queued behind a renewal reuse its token.
                if self._token is token:
                    self.refresh()
                token = self._token
        assert token is not None
        return token

    def _request(
        self,
        method: str,
        path: str,
        payload: Any = None,
        *,
        params: dict[str, Any] | None = None,
        idempotency_key: str | None = None,
    ) -> Any:
        query = {k: v for k, v in (params or {}).items() if v is not None}
        body = None if method == "GET" else (payload or {})

        def send(token: TokenSnapshot) -> httpx.Response:
            headers = {"Authorization": f"Bearer {token.access_token}"}
            if idempotency_key:
                headers["Idempotency-Key"] = idempotency_key
            return self._http.request(
                method, self._base_url + path, params=query, json=body, headers=headers
            )

        token = self._bearer()
        response = send(token)
        if response.status_code == 401:
            # Renews only if the rejected token is still active; another thread may have.
            response = send(self._bearer(stale=token))
        return _unwrap(response)

    def _list(
        self,
        path: str,
        page: int | None,
        per_page: int | None,
        query: dict[str, Any] | None = None,
    ) -> Any:
        """GETs one page of a list; query holds search, sort and filters by API name."""
        params: dict[str, Any] = {"page": page, "per_page": per_page}
        params.update({name: _encode(value) for name, value in (query or {}).items()})
        return self._request("GET", path, params=params)


class _Service:
    def __init__(self, session: _Session) -> None:
        self._s = session
