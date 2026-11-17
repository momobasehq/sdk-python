<div align=center>

<img width="75" src="https://github.com/momobasehq.png" />

# Momobase Python SDK

[![PyPI](https://img.shields.io/pypi/v/momobase.svg)](https://pypi.org/project/momobase/)
[![License](https://img.shields.io/pypi/l/momobase.svg)](LICENSE.txt)

Python client for the Momobase payment and administration APIs.

</div>

## Install

```sh
pip install momobase
```

Requires Python 3.11+.

## Usage

### Creating a new client instance

There are two clients. `MomobaseClient` authenticates an application with the
OAuth `client_credentials` grant and calls the public payment API.
`MomobaseAdminClient` authenticates an operator with the OAuth `password` grant
and covers the administration API.

```python
from momobase import MomobaseClient, MomobaseAdminClient

mb = MomobaseClient(
    base_url,
    client_id=client_id,
    client_secret=client_secret,
    token_skew_seconds=30,
)

admin = MomobaseAdminClient(
    base_url,
    email=email,
    password=password,
    access_token=None,
    refresh_token=None,
    token_skew_seconds=30,
    on_token_change=None,
)
```

Both clients authenticate lazily on the first request, cache the token, and
refresh it once when it expires or the API answers `401`. `token_skew_seconds`
is how early a token is treated as expired. `on_token_change` receives a
`TokenSnapshot` (or `None`) on every token change so an admin session can be
persisted and restored.

Clients are thread-safe. Create one per process and close it with `close()`
or a `with` block. Requests time out after 30 seconds; pass
`http_client=httpx.Client(...)` to change timeouts, proxies, or TLS settings.

### Instance methods

| Method                                                                             | Description                                                         |
| ---------------------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `mb.authenticate()`                                                                | Authenticates with the configured credentials and stores the token. |
| `mb.refresh()`                                                                     | Refreshes the session, falling back to a fresh authentication.      |
| `mb.get_token()`                                                                   | Returns the current `TokenSnapshot`, or `None`.                     |
| `mb.clear_token()`                                                                 | Clears the active session token.                                    |
| `mb.close()`                                                                       | Closes the underlying HTTP client.                                  |
| `admin.set_credentials(email, password)`                                           | Replaces the credentials and clears the current session.            |
| `admin.set_access_token(access_token, refresh_token=None, expires_in_seconds=None)` | Restores tokens obtained outside this client.                       |
| `admin.logout()`                                                                   | Ends the current administrator session and clears the token.        |

### Request options

Payment calls accept `idempotency_key=`; list calls accept `page=` and
`per_page=`. All are keyword-only.

Admin lists also filter, search and sort on the server. `q=` searches
case-insensitively, `sort=` and `order=` order the list, and `created_after=` and
`created_before=` bound the creation time (the first inclusive, the second not). Each list's own filters are exact matches, and a list of
values matches any of them. The server rejects a filter the list does not support
with a 400.

```python
admin.transactions.list(
    status=["failed", "expired"],
    app_id="app_123",
    q="256700",
    sort="amount",
    order="desc",
    created_after=datetime(2026, 1, 1, tzinfo=UTC),
    per_page=50,
)
```

## Services

> Each call returns the unwrapped API data as plain dicts, typed with the
> `TypedDict`s in `momobase.types`. 🔓 marks the application client, 🔐 the
> administrator client.

### PaymentMethodService

```python
# Lists the payment methods currently available for routing.
🔓 mb.payment_methods.list(service_type=None, country=None)
```

### CollectionService

```python
# Creates a collection (money in).
🔓 mb.collections.create(payload, idempotency_key=None)
```

### DisbursementService

```python
# Creates a disbursement (money out).
🔓 mb.disbursements.create(payload, idempotency_key=None)
```

### TransactionService

```python
# Returns a single transaction by its id.
🔓 mb.transactions.get(transaction_id)

# Returns a single transaction by the reference the application supplied.
🔓 mb.transactions.get_by_reference(reference)

# Returns a paginated, filterable transactions list across all applications.
🔐 admin.transactions.list(page=None, per_page=None, q=None, sort=None, order=None,
    created_after=None, created_before=None, status=None, service_type=None, payment_method=None,
    country=None, currency=None, app_id=None, selected_provider_account_id=None)

# Returns any application's transaction by its id.
🔐 admin.transactions.get(transaction_id)

# Returns a paginated, filterable audit logs list.
🔐 admin.transactions.audit_logs(page=None, per_page=None, q=None, sort=None,
    order=None, created_after=None, created_before=None, action=None, actor_type=None, actor_id=None,
    entity_type=None, entity_id=None)
```

### SystemService

```python
# Returns runtime metadata (version, uptime, build).
🔐 admin.system.info()

# Returns runtime health.
🔐 admin.system.health()

# Returns a paginated list of the configured background workers.
🔐 admin.system.workers(page=None, per_page=None)

# Returns a paginated list of the initialized provider runtimes.
🔐 admin.system.runtime_providers(page=None, per_page=None)
```

### AuthzService

```python
# Lists assignable permissions, optionally for one audience ("admin" | "app").
🔐 admin.authz.permissions(audience=None)

# Lists roles.
🔐 admin.authz.roles()

# Creates a role.
🔐 admin.authz.create_role(payload)

# Replaces a role.
🔐 admin.authz.update_role(name, payload)

# Deletes a custom role.
🔐 admin.authz.delete_role(name)
```

### UserService

```python
# Returns the signed-in administrator.
🔐 admin.users.me()

# Returns a paginated administrators list.
🔐 admin.users.list(page=None, per_page=None, q=None, sort=None, order=None,
    created_after=None, created_before=None, role=None, status=None)

# Creates an administrator.
🔐 admin.users.create({"name": ..., "email": ..., "password": ..., "role": ...})

# Changes an administrator password.
🔐 admin.users.change_password(user_id, password)

# Changes an administrator status ("active" | "inactive").
🔐 admin.users.change_status(user_id, status)

# Reassigns an administrator to another role.
🔐 admin.users.change_role(user_id, role)
```

### AppService

```python
# Returns a paginated applications list.
🔐 admin.apps.list(page=None, per_page=None, q=None, sort=None, order=None,
    created_after=None, created_before=None, status=None, environment=None, currency=None)

# Creates an application.
🔐 admin.apps.create({"name": ..., "description": ..., "environment": ..., "currency": ..., "charges": ...})

# Returns a single application by its id.
🔐 admin.apps.get(app_id)

# Updates an application.
🔐 admin.apps.update(app_id, payload)

# Changes an application status ("active" | "disabled" | "suspended").
🔐 admin.apps.change_status(app_id, status)

# Returns a paginated list of an application's credentials.
🔐 admin.apps.credentials(app_id, page=None, per_page=None, q=None, sort=None,
    order=None, created_after=None, created_before=None, status=None)

# Creates an application credential. The secret is returned only once.
🔐 admin.apps.create_credential(app_id, {"name": ..., "scopes": ..., "expires_at": ...})

# Revokes an application credential.
🔐 admin.apps.revoke_credential(app_id, credential_id)

# Rotates an application credential and returns the new secret.
🔐 admin.apps.rotate_credential(app_id, credential_id)
```

### ProviderService

```python
# Returns a paginated provider accounts list.
🔐 admin.providers.list(page=None, per_page=None, q=None, sort=None, order=None,
    created_after=None, created_before=None, provider_code=None, environment=None, currency=None,
    active=None)

# Returns a single provider account by its id.
🔐 admin.providers.get(account_id)

# Lists the provider codes compiled into the server.
🔐 admin.providers.registry()

# Creates a provider account.
🔐 admin.providers.create_account({
    "provider_code": ..., "name": ..., "environment": ..., "country": ...,
    "currency": ..., "charges": ..., "config": ...,
})

# Updates provider location, currency, and charges.
🔐 admin.providers.update_settings(account_id, {"country": ..., "currency": ..., "charges": ...})

# Replaces provider configuration.
🔐 admin.providers.update_config(account_id, config)

# Activates a provider account.
🔐 admin.providers.activate(account_id)

# Deactivates a provider account.
🔐 admin.providers.deactivate(account_id)

# Tests a provider account connection.
🔐 admin.providers.test(account_id)

# Returns one provider balance, optionally for a single country.
🔐 admin.providers.balance(account_id, country=None)

# Returns a paginated list of the active provider balances.
🔐 admin.providers.active_balances(page=None, per_page=None)

# Returns a paginated list of provider health snapshots.
🔐 admin.providers.health(page=None, per_page=None, q=None, sort=None, order=None,
    created_after=None, created_before=None, status=None, circuit_state=None, provider_account_id=None)
```

### RouteService

```python
# Returns a paginated payment routes list.
🔐 admin.routes.list(page=None, per_page=None, q=None, sort=None, order=None,
    created_after=None, created_before=None, service_type=None, payment_method=None,
    provider_account_id=None, active=None)

# Creates a payment route.
🔐 admin.routes.create(payload)

# Updates route priority and status.
🔐 admin.routes.update(route_id, {"priority": ..., "active": ...})
```

### AnalyticsService

```python
# Returns bucketed transaction analytics.
🔐 admin.analytics.transactions(from_=None, to=None, interval=None, app_id=None, provider_account_id=None)
```

## Errors

Every non-successful response raises a `MomobaseAPIError` carrying the HTTP
`status`, the stable Momobase `code`, and the parsed `body`. Payment calls
raise `ValueError` before sending when a required field is missing.

```python
from momobase import MomobaseAPIError

try:
    mb.collections.create(payload, idempotency_key=order_id)
except MomobaseAPIError as err:
    print(err.status, err.code)
```

## Permissions

`AdminPermissions` and `AppScopes` are enums of the known permission codes, for
autocomplete and UI gates. `permitted` tests a granted list against a required
code, honouring the `PERMISSION_WILDCARD`.

```python
from momobase import AdminPermissions, permitted

permitted(admin.users.me().get("permissions"), AdminPermissions.APPS_CREATE)
```

## Development

```sh
uv sync

uv run ruff format   # format
uv run ruff check    # lint
uv run pytest        # test
uv build             # sdist + wheel -> dist
```

## Documentation

See the [Momobase SDK documentation](https://momobasehq.github.io/sdk/) for
authentication, payment flows, administration, and the complete API.

## License

[MIT](LICENSE.txt)
