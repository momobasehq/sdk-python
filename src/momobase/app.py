from __future__ import annotations

import httpx

from ._session import _q, _Service, _Session
from .types import (
    AvailablePaymentMethods,
    CreateCollectionRequest,
    CreateDisbursementRequest,
    CreatePaymentResponse,
    OAuthTokenResponse,
    ServiceType,
    Transaction,
)


def _validate_payment(p: CreateCollectionRequest | CreateDisbursementRequest) -> None:
    # The account stays opaque: what a valid one looks like is the provider's to decide,
    # so the client only checks what the API requires of every payment.
    if not p.get("payment_method"):
        raise ValueError("payment_method is required")
    if not p.get("account"):
        raise ValueError("account is required")
    if len(p.get("country") or "") != 2:
        raise ValueError("country must be a 2-letter ISO code")


class _PaymentMethods(_Service):
    """Discovers payment methods currently available for routing."""

    def list(
        self, *, service_type: ServiceType | None = None, country: str | None = None
    ) -> AvailablePaymentMethods:
        """Lists available payment methods."""
        return self._s._request(
            "GET",
            "/api/v1/payment-methods",
            params={"service_type": service_type, "country": country},
        )


class _Collections(_Service):
    """Creates collection payments."""

    def create(
        self, payload: CreateCollectionRequest, *, idempotency_key: str | None = None
    ) -> CreatePaymentResponse:
        """Creates a collection (money in)."""
        _validate_payment(payload)
        return self._s._request(
            "POST", "/api/v1/collections", payload, idempotency_key=idempotency_key
        )


class _Disbursements(_Service):
    """Creates disbursement payments."""

    def create(
        self, payload: CreateDisbursementRequest, *, idempotency_key: str | None = None
    ) -> CreatePaymentResponse:
        """Creates a disbursement (money out)."""
        _validate_payment(payload)
        return self._s._request(
            "POST", "/api/v1/disbursements", payload, idempotency_key=idempotency_key
        )


class _Transactions(_Service):
    """Reads application transactions."""

    def get(self, transaction_id: str) -> Transaction:
        """Gets a transaction by ID."""
        return self._s._request("GET", f"/api/v1/transactions/{_q(transaction_id)}")

    def get_by_reference(self, reference: str) -> Transaction:
        """Gets a transaction by the reference the application supplied."""
        return self._s._request(
            "GET", f"/api/v1/transactions/by-reference/{_q(reference)}"
        )


class MomobaseClient(_Session):
    """Calls application-authenticated Momobase endpoints."""

    _refresh_path = "/api/v1/token/refresh"

    def __init__(
        self,
        base_url: str,
        *,
        client_id: str,
        client_secret: str,
        token_skew_seconds: float = 30,
        http_client: httpx.Client | None = None,
    ) -> None:
        super().__init__(base_url, token_skew_seconds, http_client)
        self._client_id = client_id
        self._client_secret = client_secret
        self.payment_methods = _PaymentMethods(self)
        self.collections = _Collections(self)
        self.disbursements = _Disbursements(self)
        self.transactions = _Transactions(self)

    def authenticate(self) -> OAuthTokenResponse:
        """Authenticates with the configured application credential."""
        return self._form(
            "/api/v1/token",
            {
                "grant_type": "client_credentials",
                "client_id": self._client_id,
                "client_secret": self._client_secret,
            },
        )
