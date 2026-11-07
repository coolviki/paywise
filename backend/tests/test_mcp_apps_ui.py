"""MCP Apps: tools advertise their UI, and the UI resources are served correctly."""
from tests.conftest import jwt_headers, mcp_call

APP_MIME = "text/html;profile=mcp-app"
EXPECTED = {
    "recommend_card": "ui://paywise/card-ranking.html",
    "get_restaurant_offers": "ui://paywise/restaurant-offers.html",
}


def _key(client, user):
    return client.post("/api/mcp-keys", json={"name": "t"}, headers=jwt_headers(user)).json()["api_key"]


def test_tools_link_to_ui_resources(client, seed):
    key = _key(client, seed["alice"])
    tools = {t["name"]: t for t in mcp_call(client, key, "tools/list").json()["result"]["tools"]}
    for name, uri in EXPECTED.items():
        meta = tools[name].get("_meta") or {}
        assert meta["ui"]["resourceUri"] == uri
        assert meta["ui/resourceUri"] == uri  # legacy key
    # plain tools stay plain
    assert "ui" not in (tools["list_my_cards"].get("_meta") or {})


def test_ui_resources_are_listed_and_served_as_mcp_apps(client, seed):
    key = _key(client, seed["alice"])
    listed = {r["uri"]: r for r in mcp_call(client, key, "resources/list").json()["result"]["resources"]}
    for uri in EXPECTED.values():
        assert listed[uri]["mimeType"] == APP_MIME
        res = mcp_call(client, key, "resources/read", {"uri": uri}).json()["result"]["contents"][0]
        assert res["mimeType"] == APP_MIME
        html = res["text"]
        # self-contained: no external scripts/styles, and speaks the MCP Apps lifecycle
        assert "<script src" not in html and "<link" not in html
        for marker in ("ui/initialize", "ui/notifications/initialized", "ui/notifications/tool-result",
                       "ui/notifications/size-changed", "2026-01-26"):
            assert marker in html, marker


def test_ui_resources_require_auth(client, seed):
    r = mcp_call(client, None, "resources/read", {"uri": "ui://paywise/card-ranking.html"})
    assert r.status_code == 401
