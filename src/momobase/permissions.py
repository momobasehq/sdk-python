from collections.abc import Collection
from enum import StrEnum


class AdminPermissions(StrEnum):
    """Known administrator permission codes for autocomplete and UI gates."""

    SYSTEM_READ = "system:read"
    TRANSACTIONS_READ = "transactions:read"
    AUDIT_READ = "audit:read"
    USERS_READ = "users:read"
    USERS_CREATE = "users:create"
    USERS_UPDATE = "users:update"
    ROLES_READ = "roles:read"
    ROLES_CREATE = "roles:create"
    ROLES_UPDATE = "roles:update"
    ROLES_DELETE = "roles:delete"
    APPS_READ = "apps:read"
    APPS_CREATE = "apps:create"
    APPS_UPDATE = "apps:update"
    APPS_TEST = "apps:test"
    CREDENTIALS_READ = "credentials:read"
    CREDENTIALS_CREATE = "credentials:create"
    CREDENTIALS_UPDATE = "credentials:update"
    PROVIDERS_READ = "providers:read"
    PROVIDERS_CREATE = "providers:create"
    PROVIDERS_UPDATE = "providers:update"
    PROVIDERS_TEST = "providers:test"
    BALANCES_READ = "balances:read"
    ROUTES_READ = "routes:read"
    ROUTES_CREATE = "routes:create"
    ROUTES_UPDATE = "routes:update"


class AppScopes(StrEnum):
    """The scopes an application credential may hold."""

    COLLECTIONS_CREATE = "collections:create"
    DISBURSEMENTS_CREATE = "disbursements:create"
    TRANSACTIONS_READ = "transactions:read"


PERMISSION_WILDCARD = "*"
"""Grants every permission in an audience."""


def permitted(held: Collection[str] | None, required: str) -> bool:
    """Reports whether held permissions satisfy a required code."""
    return held is not None and (required in held or PERMISSION_WILDCARD in held)
