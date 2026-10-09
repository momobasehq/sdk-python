import httpx
import pytest

from momobase import MomobaseAPIError, MomobaseClient

PAYMENT = {
    "payment_method": "momo",
    "account": "256700000000",
    "amount": 5000,
    "currency": "UGX",
    "country": "UG",
    "reference": "order-1",
}


def client(handler):
    return MomobaseClient(
        "https://mb.test/",
        client_id="id",
        client_secret="secret",
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )


def issued(n):
    token = {"access_token": f"a{n}", "refresh_token": f"r{n}", "expires_in": 3600}
    return httpx.Response(200, json={**token, "token_type": "Bearer"})


def test_authenticates_lazily_and_unwraps_envelope():
    seen = []

    def handler(req):
        seen.append((req.url.raw_path.decode(), req.headers.get("authorization")))
        if req.url.path == "/api/v1/token":
            return issued(1)
        return httpx.Response(200, json={"success": True, "data": {"id": "tx/1"}})

    with client(handler) as mb:
        assert mb.transactions.get("tx/1") == {"id": "tx/1"}
    assert seen == [
        ("/api/v1/token", None),
        ("/api/v1/transactions/tx%2F1", "Bearer a1"),
    ]


def test_refreshes_once_on_401_and_retries():
    seen = []

    def handler(req):
        seen.append(req.url.path)
        if req.url.path == "/api/v1/token":
            return issued(1)
        if req.url.path == "/api/v1/token/refresh":
            assert b"refresh_token=r1" in req.content
            return issued(2)
        if req.headers["authorization"] == "Bearer a1":
            return httpx.Response(401)
        return httpx.Response(200, json={"success": True, "data": {"ok": True}})

    with client(handler) as mb:
        assert mb.transactions.get_by_reference("order-1") == {"ok": True}
        assert mb.get_token().access_token == "a2"
    ref = "/api/v1/transactions/by-reference/order-1"
    assert seen == ["/api/v1/token", ref, "/api/v1/token/refresh", ref]


def test_failed_refresh_reauthenticates_and_errors_carry_code():
    tokens = iter([issued(1), issued(2)])
    keys = []

    def handler(req):
        if req.url.path == "/api/v1/token":
            return next(tokens)
        if req.url.path == "/api/v1/token/refresh":
            return httpx.Response(400, json={"error": "invalid_grant"})
        keys.append(req.headers.get("idempotency-key"))
        if req.headers["authorization"] == "Bearer a1":
            return httpx.Response(401)
        error = {"code": "VALIDATION_ERROR", "message": "bad amount"}
        return httpx.Response(422, json={"success": False, "error": error})

    with client(handler) as mb:
        with pytest.raises(ValueError):
            mb.collections.create({**PAYMENT, "country": "UGA"})
        with pytest.raises(MomobaseAPIError) as err:
            mb.collections.create(PAYMENT, idempotency_key="k1")
    assert (err.value.status, err.value.code, str(err.value)) == (
        422,
        "VALIDATION_ERROR",
        "bad amount",
    )
    assert keys == ["k1", "k1"]
