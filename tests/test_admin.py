from datetime import UTC, datetime

import httpx

from momobase import MomobaseAdminClient

PAGE = {"page": 1, "total": 0, "items": [], "count": 0}


def admin(handler):
    return MomobaseAdminClient(
        "https://mb.test/",
        access_token="a1",
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )


def test_list_filters_encode_as_the_api_expects():
    seen = []

    def handler(req):
        seen.append((req.url.path, dict(req.url.params)))
        return httpx.Response(200, json={"success": True, "data": PAGE})

    with admin(handler) as mb:
        mb.transactions.list(
            per_page=50,
            q="2567",
            sort="amount",
            order="desc",
            created_after=datetime(2026, 1, 1, tzinfo=UTC),
            status=["failed", "expired"],
            app_id="app_1",
            country=[],  # an empty filter is left out rather than sent blank
        )
        mb.providers.list(active=False)
    assert seen == [
        (
            "/api/admin/transactions",
            {
                "per_page": "50",
                "q": "2567",
                "sort": "amount",
                "order": "desc",
                "from": "2026-01-01T00:00:00+00:00",
                "status": "failed,expired",
                "app_id": "app_1",
            },
        ),
        ("/api/admin/providers", {"active": "false"}),
    ]


def test_gets_one_transaction_by_id():
    def handler(req):
        assert req.url.raw_path.decode() == "/api/admin/transactions/tx%2F1"
        return httpx.Response(200, json={"success": True, "data": {"id": "tx/1"}})

    with admin(handler) as mb:
        assert mb.transactions.get("tx/1") == {"id": "tx/1"}
