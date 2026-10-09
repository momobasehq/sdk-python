from __future__ import annotations

from collections.abc import Callable
from typing import Any

import httpx

from ._session import TokenSnapshot, _q, _Service, _Session
from .types import (
    AdminTransaction,
    AdminUser,
    AnalyticsInterval,
    App,
    AppCredential,
    AppStatus,
    AuditLog,
    CreateAppRequest,
    CreateCredentialRequest,
    CreatedCredential,
    CreateProviderAccountRequest,
    CreateRoleRequest,
    CreateRouteRequest,
    CreateUserRequest,
    OAuthTokenResponse,
    PaginatedData,
    PaymentRoute,
    PermissionAudience,
    PermissionList,
    ProviderAccount,
    ProviderBalance,
    ProviderBalanceResult,
    ProviderHealthSnapshot,
    ProviderRegistry,
    ProviderSettings,
    Role,
    RoleList,
    RoleRequest,
    RuntimeProvider,
    SystemHealth,
    SystemInfo,
    TransactionAnalytics,
    UpdateAppRequest,
    UpdateRouteRequest,
    UserStatus,
    WorkerState,
)

_ACCOUNTS = "/api/admin/providers/accounts"


class _System(_Service):
    """Reads system health and runtime state."""

    def info(self) -> SystemInfo:
        """Returns runtime metadata (version, uptime, build)."""
        return self._s._request("GET", "/api/admin/system/info")

    def health(self) -> SystemHealth:
        """Returns runtime health."""
        return self._s._request("GET", "/api/admin/system/health")

    def workers(
        self, *, page: int | None = None, per_page: int | None = None
    ) -> PaginatedData[WorkerState]:
        """Lists the configured background workers."""
        return self._s._list("/api/admin/workers", page, per_page)

    def runtime_providers(
        self, *, page: int | None = None, per_page: int | None = None
    ) -> PaginatedData[RuntimeProvider]:
        """Lists the initialized provider runtimes."""
        return self._s._list("/api/admin/runtime/providers", page, per_page)


class _Authz(_Service):
    """Manages permissions and roles."""

    def permissions(self, audience: PermissionAudience | None = None) -> PermissionList:
        """Lists assignable permissions, optionally for one audience."""
        return self._s._request(
            "GET", "/api/admin/permissions", params={"audience": audience}
        )

    def roles(self) -> RoleList:
        """Lists roles."""
        return self._s._request("GET", "/api/admin/roles")

    def create_role(self, payload: CreateRoleRequest) -> Role:
        """Creates a role."""
        return self._s._request("POST", "/api/admin/roles", payload)

    def update_role(self, name: str, payload: RoleRequest) -> Any:
        """Replaces a role."""
        return self._s._request("PATCH", f"/api/admin/roles/{_q(name)}", payload)

    def delete_role(self, name: str) -> Any:
        """Deletes a custom role."""
        return self._s._request("DELETE", f"/api/admin/roles/{_q(name)}")


class _Users(_Service):
    """Manages administrators."""

    def me(self) -> AdminUser:
        """Returns the signed-in administrator."""
        return self._s._request("GET", "/api/admin/me")

    def list(
        self, *, page: int | None = None, per_page: int | None = None
    ) -> PaginatedData[AdminUser]:
        """Lists administrators."""
        return self._s._list("/api/admin/users", page, per_page)

    def create(self, payload: CreateUserRequest) -> AdminUser:
        """Creates an administrator."""
        return self._s._request("POST", "/api/admin/users", payload)

    def change_password(self, user_id: str, password: str) -> Any:
        """Changes an administrator password."""
        return self._s._request(
            "PATCH", f"/api/admin/users/{_q(user_id)}/password", {"password": password}
        )

    def change_status(self, user_id: str, status: UserStatus) -> Any:
        """Changes an administrator status."""
        return self._s._request(
            "PATCH", f"/api/admin/users/{_q(user_id)}/status", {"status": status}
        )

    def change_role(self, user_id: str, role: str) -> Any:
        """Reassigns an administrator to another role."""
        return self._s._request(
            "PATCH", f"/api/admin/users/{_q(user_id)}/role", {"role": role}
        )


class _Apps(_Service):
    """Manages applications and credentials."""

    def list(
        self, *, page: int | None = None, per_page: int | None = None
    ) -> PaginatedData[App]:
        """Lists applications."""
        return self._s._list("/api/admin/apps", page, per_page)

    def create(self, payload: CreateAppRequest) -> App:
        """Creates an application."""
        return self._s._request("POST", "/api/admin/apps", payload)

    def get(self, app_id: str) -> App:
        """Gets an application."""
        return self._s._request("GET", f"/api/admin/apps/{_q(app_id)}")

    def update(self, app_id: str, payload: UpdateAppRequest) -> App:
        """Updates an application."""
        return self._s._request("PATCH", f"/api/admin/apps/{_q(app_id)}", payload)

    def change_status(self, app_id: str, status: AppStatus) -> Any:
        """Changes an application status."""
        return self._s._request(
            "PATCH", f"/api/admin/apps/{_q(app_id)}/status", {"status": status}
        )

    def credentials(
        self, app_id: str, *, page: int | None = None, per_page: int | None = None
    ) -> PaginatedData[AppCredential]:
        """Lists an application's credentials."""
        return self._s._list(f"/api/admin/apps/{_q(app_id)}/credentials", page, per_page)

    def create_credential(
        self, app_id: str, payload: CreateCredentialRequest | None = None
    ) -> CreatedCredential:
        """Creates an application credential. The secret is returned only once."""
        return self._s._request(
            "POST", f"/api/admin/apps/{_q(app_id)}/credentials", payload
        )

    def revoke_credential(self, app_id: str, credential_id: str) -> Any:
        """Revokes an application credential."""
        return self._s._request(
            "PATCH",
            f"/api/admin/apps/{_q(app_id)}/credentials/{_q(credential_id)}/revoke",
        )

    def rotate_credential(self, app_id: str, credential_id: str) -> CreatedCredential:
        """Rotates an application credential and returns the new secret."""
        return self._s._request(
            "POST",
            f"/api/admin/apps/{_q(app_id)}/credentials/{_q(credential_id)}/rotate",
        )


class _Providers(_Service):
    """Manages provider accounts and runtime status."""

    def list(
        self, *, page: int | None = None, per_page: int | None = None
    ) -> PaginatedData[ProviderAccount]:
        """Lists provider accounts."""
        return self._s._list("/api/admin/providers", page, per_page)

    def get(self, account_id: str) -> ProviderAccount:
        """Gets a provider account."""
        return self._s._request("GET", f"{_ACCOUNTS}/{_q(account_id)}")

    def registry(self) -> ProviderRegistry:
        """Lists the provider codes compiled into the server."""
        return self._s._request("GET", "/api/admin/providers/registry")

    def create_account(self, payload: CreateProviderAccountRequest) -> ProviderAccount:
        """Creates a provider account."""
        return self._s._request("POST", _ACCOUNTS, payload)

    def update_settings(self, account_id: str, payload: ProviderSettings) -> Any:
        """Updates provider location, currency, and charges."""
        return self._s._request(
            "PATCH", f"{_ACCOUNTS}/{_q(account_id)}/settings", payload
        )

    def update_config(self, account_id: str, config: dict[str, Any]) -> Any:
        """Replaces provider configuration."""
        return self._s._request(
            "PATCH", f"{_ACCOUNTS}/{_q(account_id)}/config", {"config": config}
        )

    def activate(self, account_id: str) -> Any:
        """Activates a provider account."""
        return self._s._request("PATCH", f"{_ACCOUNTS}/{_q(account_id)}/activate")

    def deactivate(self, account_id: str) -> Any:
        """Deactivates a provider account."""
        return self._s._request("PATCH", f"{_ACCOUNTS}/{_q(account_id)}/deactivate")

    def test(self, account_id: str) -> Any:
        """Tests a provider account connection."""
        return self._s._request("POST", f"{_ACCOUNTS}/{_q(account_id)}/test")

    def balance(self, account_id: str, country: str | None = None) -> ProviderBalance:
        """Gets one provider balance, optionally for a single country."""
        return self._s._request(
            "GET", f"{_ACCOUNTS}/{_q(account_id)}/balance", params={"country": country}
        )

    def active_balances(
        self, *, page: int | None = None, per_page: int | None = None
    ) -> PaginatedData[ProviderBalanceResult]:
        """Lists the active provider balances."""
        return self._s._list("/api/admin/balances/providers", page, per_page)

    def health(
        self, *, page: int | None = None, per_page: int | None = None
    ) -> PaginatedData[ProviderHealthSnapshot]:
        """Lists provider health snapshots."""
        return self._s._list("/api/admin/health/providers", page, per_page)


class _Routes(_Service):
    """Manages payment routes."""

    def list(
        self, *, page: int | None = None, per_page: int | None = None
    ) -> PaginatedData[PaymentRoute]:
        """Lists payment routes."""
        return self._s._list("/api/admin/routes", page, per_page)

    def create(self, payload: CreateRouteRequest) -> PaymentRoute:
        """Creates a payment route."""
        return self._s._request("POST", "/api/admin/routes", payload)

    def update(self, route_id: str, payload: UpdateRouteRequest) -> Any:
        """Updates route priority and status."""
        return self._s._request("PATCH", f"/api/admin/routes/{_q(route_id)}", payload)


class _Transactions(_Service):
    """Reads transactions and audit logs."""

    def list(
        self, *, page: int | None = None, per_page: int | None = None
    ) -> PaginatedData[AdminTransaction]:
        """Lists transactions across all applications."""
        return self._s._list("/api/admin/transactions", page, per_page)

    def audit_logs(
        self, *, page: int | None = None, per_page: int | None = None
    ) -> PaginatedData[AuditLog]:
        """Lists audit logs."""
        return self._s._list("/api/admin/audit-logs", page, per_page)


class _Analytics(_Service):
    """Reads transaction analytics."""

    def transactions(
        self,
        *,
        from_: str | None = None,
        to: str | None = None,
        interval: AnalyticsInterval | None = None,
        app_id: str | None = None,
        provider_account_id: str | None = None,
    ) -> TransactionAnalytics:
        """Gets bucketed transaction analytics."""
        return self._s._request(
            "GET",
            "/api/admin/analytics/transactions",
            params={
                "from": from_,
                "to": to,
                "interval": interval,
                "app_id": app_id,
                "provider_account_id": provider_account_id,
            },
        )


class MomobaseAdminClient(_Session):
    """Calls administrator-authenticated Momobase endpoints."""

    _refresh_path = "/api/admin/token/refresh"

    def __init__(
        self,
        base_url: str,
        *,
        email: str | None = None,
        password: str | None = None,
        access_token: str | None = None,
        refresh_token: str | None = None,
        token_skew_seconds: float = 30,
        on_token_change: Callable[[TokenSnapshot | None], None] | None = None,
        http_client: httpx.Client | None = None,
    ) -> None:
        super().__init__(base_url, token_skew_seconds, http_client)
        self._email = email
        self._password = password
        self._on_token_change = on_token_change
        if access_token:
            self.set_access_token(access_token, refresh_token)
        self.system = _System(self)
        self.authz = _Authz(self)
        self.users = _Users(self)
        self.apps = _Apps(self)
        self.providers = _Providers(self)
        self.routes = _Routes(self)
        self.transactions = _Transactions(self)
        self.analytics = _Analytics(self)

    def set_credentials(self, email: str, password: str) -> None:
        """Replaces the credentials and clears the current session."""
        self._email = email
        self._password = password
        self.clear_token()

    def set_access_token(
        self,
        access_token: str,
        refresh_token: str | None = None,
        expires_in_seconds: float | None = None,
    ) -> None:
        """Restores tokens obtained outside this client."""
        self._set_token(access_token, refresh_token, expires_in_seconds)

    def authenticate(self) -> OAuthTokenResponse:
        """Authenticates with the configured administrator credentials."""
        if not self._email or not self._password:
            raise ValueError("Admin email and password are required")
        return self._form(
            "/api/admin/token",
            {
                "grant_type": "password",
                "username": self._email,
                "password": self._password,
            },
        )

    def logout(self) -> None:
        """Ends the current administrator session and clears the token."""
        self._request("POST", "/api/admin/logout")
        self.clear_token()
