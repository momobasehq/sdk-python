"""Request and response shapes of the Momobase API, as plain dicts."""

from collections.abc import Sequence
from typing import Any, Generic, Literal, NotRequired, TypedDict, TypeVar

T = TypeVar("T")

PaymentMethod = Literal["momo", "card", "bank_transfer", "wallet"]
ServiceType = Literal["collection", "disbursement"]
TransactionStatus = Literal[
    "pending", "processing", "succeeded", "failed", "unknown", "cancelled", "expired"
]
Environment = Literal["sandbox", "production"]
PermissionAudience = Literal["admin", "app"]
UserStatus = Literal["active", "inactive"]
AppStatus = Literal["active", "disabled", "suspended"]
AnalyticsInterval = Literal["day", "hour"]
SortOrder = Literal["asc", "desc"]
# A filter takes one value, or several to match any of them.
OneOrMany = T | Sequence[T]
TransactionSort = Literal["created_at", "amount", "status", "updated_at"]
AuditLogSort = Literal["created_at", "action"]
AppSort = Literal["name", "status", "created_at"]
CredentialSort = Literal["name", "status", "last_used_at", "created_at"]
UserSort = Literal["name", "email", "created_at"]
ProviderAccountSort = Literal["name", "provider_code", "updated_at", "created_at"]
ProviderHealthSort = Literal["latency_ms", "consecutive_failures", "updated_at"]
RouteSort = Literal["priority", "created_at"]


class ChargeRule(TypedDict):
    """Defines one fee: a flat amount plus a percentage of the transaction amount."""

    flat: int
    """Fixed fee in currency minor units."""
    percentage: int
    """Proportional fee in basis points (100 = 1%), at most 10,000."""


class ChargeSchedule(TypedDict):
    """Defines collection and disbursement charges."""

    collection: ChargeRule
    disbursement: ChargeRule


class PaginatedData(TypedDict, Generic[T]):
    """Contains one page of API results."""

    page: int
    total: int
    items: list[T]
    count: int


class OAuthTokenResponse(TypedDict):
    """Contains OAuth access and refresh tokens."""

    access_token: str
    token_type: str
    expires_in: int
    refresh_token: NotRequired[str]
    scope: NotRequired[str]
    app_id: NotRequired[str]
    app_name: NotRequired[str]
    credential_id: NotRequired[str]
    client_id: NotRequired[str]


class PartyPayload(TypedDict, total=False):
    """Describes a payment customer or recipient."""

    name: str
    email: str


class AvailablePaymentMethod(TypedDict):
    """Describes one currently routable payment method."""

    service_type: ServiceType
    payment_method: PaymentMethod


class AvailablePaymentMethods(TypedDict):
    """Contains currently routable payment methods."""

    items: list[AvailablePaymentMethod]
    count: int


class _PaymentRequest(TypedDict):
    # `account` and `scheme` are provider-specific (mobile number, bank account, card
    # token, wallet address) and validated by the provider the payment routes to.
    payment_method: PaymentMethod
    scheme: NotRequired[str]
    account: str
    amount: float
    currency: str
    country: str
    reference: str
    description: NotRequired[str]
    metadata: NotRequired[dict[str, Any]]


class CreateCollectionRequest(_PaymentRequest):
    """Creates a collection payment."""

    customer: NotRequired[PartyPayload]


class CreateDisbursementRequest(_PaymentRequest):
    """Creates a disbursement payment."""

    recipient: NotRequired[PartyPayload]


class CreatePaymentResponse(TypedDict):
    """Describes a newly created payment."""

    transaction_id: str
    reference: str
    service_type: ServiceType
    payment_method: PaymentMethod
    status: TransactionStatus
    selected_provider: str
    provider_reference: str
    platform_fee: float
    message: str


class Transaction(TypedDict):
    """Describes an application-visible transaction."""

    id: str
    app_id: str
    service_type: ServiceType
    payment_method: PaymentMethod
    amount: float
    currency: str
    country: NotRequired[str]
    reference: str
    idempotency_key: str
    status: TransactionStatus
    selected_route_id: NotRequired[str]
    selected_provider_account_id: NotRequired[str]
    provider_reference: NotRequired[str]
    customer_account: NotRequired[str]
    customer_email: NotRequired[str]
    customer_name: NotRequired[str]
    description: NotRequired[str]
    platform_fee: float
    created_at: str
    updated_at: str


class AdminTransaction(Transaction):
    """Describes a transaction with administrator fields."""

    provider_fee: float
    reconciliation_attempts: int
    last_reconciled_at: NotRequired[str]
    next_reconcile_at: NotRequired[str]


class Permission(TypedDict):
    """Describes one server permission."""

    id: str
    code: str
    audience: PermissionAudience
    description: str
    created_at: str
    updated_at: str


class PermissionList(TypedDict):
    """Contains the permission catalogue."""

    items: list[Permission]
    count: int


class Role(TypedDict):
    """Describes a named set of administrator permissions."""

    id: str
    name: str
    description: str
    system: bool
    permissions: list[Permission]
    created_at: str
    updated_at: str


class RoleList(TypedDict):
    """Contains available administrator roles."""

    items: list[Role]
    count: int


class RoleRequest(TypedDict):
    """Replaces a role."""

    name: NotRequired[str]
    description: NotRequired[str]
    permissions: list[str]


class CreateRoleRequest(TypedDict):
    """Creates a role."""

    name: str
    description: NotRequired[str]
    permissions: list[str]


class AdminUser(TypedDict):
    """Describes an administrator and effective permissions."""

    id: str
    name: str
    email: str
    role: str
    status: str
    permissions: NotRequired[list[str]]
    created_at: str
    updated_at: str


class CreateUserRequest(TypedDict):
    """Creates an administrator."""

    name: str
    email: str
    password: str
    role: NotRequired[str]


class App(TypedDict):
    """Describes a Momobase application."""

    id: str
    name: str
    description: str
    status: str
    environment: str
    currency: str
    charges: ChargeSchedule
    created_by: NotRequired[str]
    created_at: str
    updated_at: str


class CreateAppRequest(TypedDict):
    """Creates an application."""

    name: str
    description: NotRequired[str]
    environment: NotRequired[Environment]
    currency: str
    charges: NotRequired[ChargeSchedule]


class UpdateAppRequest(TypedDict, total=False):
    """Updates an application."""

    name: str
    description: str
    environment: Environment
    currency: str
    charges: ChargeSchedule


class AppCredential(TypedDict):
    """Describes an application OAuth credential."""

    id: str
    app_id: str
    name: str
    client_id: str
    status: str
    scopes: str
    last_used_at: NotRequired[str]
    expires_at: NotRequired[str]
    created_by: NotRequired[str]
    created_at: str
    updated_at: str


class CreateCredentialRequest(TypedDict, total=False):
    """Creates an application credential."""

    name: str
    scopes: str
    expires_at: str


class CreatedCredential(TypedDict):
    """Returns a newly created credential and its one-time secret."""

    credential: AppCredential
    client_secret: str


class ProviderAccount(TypedDict):
    """Describes a configured provider account."""

    id: str
    provider_code: str
    name: str
    environment: str
    country: str
    currency: str
    charges: ChargeSchedule
    active: bool
    config_version: int
    config_hash: str
    created_at: str
    updated_at: str


class CreateProviderAccountRequest(TypedDict):
    """Creates a provider account. `config` must carry a `webhook_secret`."""

    provider_code: str
    name: str
    environment: Environment
    country: str
    currency: str
    charges: NotRequired[ChargeSchedule]
    config: dict[str, Any]


class ProviderSettings(TypedDict):
    """Updates provider location, currency, and charges."""

    country: str
    currency: str
    charges: ChargeSchedule


class ProviderCapability(TypedDict):
    """Describes one service and payment-method capability."""

    service_type: ServiceType
    payment_method: PaymentMethod


class ProviderRegistry(TypedDict):
    """Provider codes registered in the running server, including custom providers."""

    providers: list[str]


class PaymentRoute(TypedDict):
    """Describes a payment route."""

    id: str
    service_type: ServiceType
    payment_method: PaymentMethod
    provider_account_id: str
    provider_name: str
    priority: int
    active: bool
    created_at: str
    updated_at: str


class CreateRouteRequest(TypedDict):
    """Creates a payment route."""

    service_type: ServiceType
    payment_method: PaymentMethod
    provider_account_id: str
    priority: int
    active: bool


class UpdateRouteRequest(TypedDict):
    """Updates route priority and status."""

    priority: int
    active: bool


class ProviderHealthSnapshot(TypedDict):
    """Describes the latest provider health check."""

    provider_account_id: str
    provider_name: str
    status: str
    circuit_state: str
    last_checked_at: NotRequired[str]
    last_success_at: NotRequired[str]
    last_failure_at: NotRequired[str]
    consecutive_failures: int
    latency_ms: int
    collections_available: bool
    disbursements_available: bool
    balance_query_available: bool
    last_error_code: NotRequired[str]
    last_error_message: NotRequired[str]
    created_at: NotRequired[str]
    updated_at: NotRequired[str]


class AuditLog(TypedDict):
    """Describes an administrator audit entry."""

    id: str
    actor_id: str
    actor_type: str
    action: str
    entity_type: str
    entity_id: str
    metadata_json: str
    ip_address: str
    user_agent: str
    created_at: str
    updated_at: str


class RuntimeProvider(TypedDict):
    """Describes an initialized provider runtime."""

    provider_account_id: str
    provider_name: str
    provider_code: str
    config_version: int
    active: bool
    initialized: bool
    capabilities: list[ProviderCapability]
    country: str
    currency: str
    health: NotRequired[ProviderHealthSnapshot]


class ProviderBalance(TypedDict):
    """Describes available and ledger provider balances."""

    currency: str
    available: float
    ledger: float


class ProviderBalanceResult(TypedDict):
    """Describes one provider balance query result."""

    provider_account_id: str
    provider_code: NotRequired[str]
    country: str
    status: str
    balance: NotRequired[ProviderBalance]
    error: NotRequired[str]


class SystemInfo(TypedDict):
    """Describes server runtime metadata."""

    app_name: str
    app_env: str
    db_type: str
    addr: str
    workers_enabled: bool
    worker_names: list[str]
    go_version: str
    server_time: str


class SystemHealth(TypedDict):
    """Describes server and database health."""

    ok: bool
    database: str
    runtime_provider_count: int
    active_provider_account_count: int
    workers_configured: list[str]
    server_time: str


class WorkerState(TypedDict):
    """Describes one background worker."""

    name: str
    configured: bool
    state: str


class ServiceCounts(TypedDict):
    """Transaction counts for one bucket, split by service."""

    collection: int
    disbursement: int


class AnalyticsBucket(TypedDict):
    """Describes one transaction analytics time bucket."""

    period: str
    total: int
    by_service: ServiceCounts
    succeeded: int
    failed: int


class CurrencyVolume(TypedDict):
    """Describes payment volume for one currency."""

    currency: str
    count: int
    amount: float


# Functional form because `from` is a Python keyword.
TransactionAnalytics = TypedDict(
    "TransactionAnalytics",
    {
        "from": str,
        "to": str,
        "interval": AnalyticsInterval,
        "buckets": list[AnalyticsBucket],
        "total": int,
        "by_service": ServiceCounts,
        "volume": list[CurrencyVolume],
    },
)
