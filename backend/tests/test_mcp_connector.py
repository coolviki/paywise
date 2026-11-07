from app.models import McpApiKey
from tests.conftest import call_tool, jwt_headers, mcp_call


def _create_key(client, user, name="Claude"):
    r = client.post("/api/mcp-keys", json={"name": name}, headers=jwt_headers(user))
    assert r.status_code == 201, r.text
    return r.json()


# --- Key management API ----------------------------------------------------

def test_create_key_returns_raw_key_once_and_stores_only_hash(client, db, seed):
    created = _create_key(client, seed["alice"], "My phone")
    assert created["api_key"].startswith("pw_live_")
    assert created["key_prefix"] == created["api_key"][:12]

    record = db.query(McpApiKey).one()
    assert record.key_hash != created["api_key"]
    assert created["api_key"] not in (record.key_hash, record.key_prefix)

    listed = client.get("/api/mcp-keys", headers=jwt_headers(seed["alice"])).json()
    assert len(listed) == 1 and "api_key" not in listed[0]


def test_user_cannot_see_or_revoke_another_users_key(client, seed):
    alice_key = _create_key(client, seed["alice"])
    assert client.get("/api/mcp-keys", headers=jwt_headers(seed["bob"])).json() == []
    r = client.delete(f"/api/mcp-keys/{alice_key['id']}", headers=jwt_headers(seed["bob"]))
    assert r.status_code == 404
    # still works for Alice
    assert call_tool(client, alice_key["api_key"], "list_my_cards")["count"] == 2


def test_key_limit(client, seed):
    for i in range(5):
        _create_key(client, seed["alice"], f"k{i}")
    r = client.post("/api/mcp-keys", json={"name": "one too many"}, headers=jwt_headers(seed["alice"]))
    assert r.status_code == 409


# --- MCP auth --------------------------------------------------------------

def test_mcp_rejects_missing_and_bad_keys(client, seed):
    assert mcp_call(client, None, "tools/list").status_code == 401
    assert mcp_call(client, "pw_live_not-a-real-key", "tools/list").status_code == 401
    # a normal app JWT is not accepted on /mcp
    jwt = jwt_headers(seed["alice"])["Authorization"][7:]
    assert mcp_call(client, jwt, "tools/list").status_code == 401


def test_revoked_key_stops_working(client, seed):
    key = _create_key(client, seed["alice"])
    assert mcp_call(client, key["api_key"], "tools/list").status_code == 200
    client.delete(f"/api/mcp-keys/{key['id']}", headers=jwt_headers(seed["alice"]))
    assert mcp_call(client, key["api_key"], "tools/list").status_code == 401


def test_tools_are_read_only_and_take_no_user_argument(client, seed):
    key = _create_key(client, seed["alice"])["api_key"]
    tools = mcp_call(client, key, "tools/list").json()["result"]["tools"]
    assert {t["name"] for t in tools} == {"list_my_cards", "recommend_card", "get_card_offers", "find_place", "get_restaurant_offers"}
    for t in tools:
        assert t["annotations"]["readOnlyHint"] is True
        props = set(t["inputSchema"].get("properties", {}))
        assert not props & {"user_id", "user", "email", "ctx"}, (t["name"], props)


# --- User isolation (the important one) ------------------------------------

def test_each_key_only_sees_its_owners_cards(client, seed):
    alice_key = _create_key(client, seed["alice"])["api_key"]
    bob_key = _create_key(client, seed["bob"])["api_key"]

    alice_cards = {c["card_name"] for c in call_tool(client, alice_key, "list_my_cards")["cards"]}
    bob_cards = {c["card_name"] for c in call_tool(client, bob_key, "list_my_cards")["cards"]}
    assert alice_cards == {"HDFC Diners Club Black", "Tata Neu Infinity HDFC"}
    assert bob_cards == {"SBI Cashback"}

    alice_rank = {r["card_name"] for r in call_tool(client, alice_key, "recommend_card", {"merchant": "Croma"})["ranking"]}
    assert "SBI Cashback" not in alice_rank

    alice_offers = call_tool(client, alice_key, "get_card_offers", {"merchant": "Croma"})["offers"]
    bob_offers = call_tool(client, bob_key, "get_card_offers", {"merchant": "Croma"})["offers"]
    assert {o["card_name"] for o in alice_offers} == {"HDFC Diners Club Black"}
    assert {o["card_name"] for o in bob_offers} == {"SBI Cashback"}


def test_extra_user_id_argument_is_ignored(client, seed):
    """Even if Claude is tricked into passing someone else's id, it has no effect."""
    alice_key = _create_key(client, seed["alice"])["api_key"]
    r = mcp_call(client, alice_key, "tools/call",
                 {"name": "list_my_cards", "arguments": {"user_id": str(seed["bob"].id)}})
    body = r.json()
    if "result" in body and not body["result"].get("isError"):
        import json
        names = {c["card_name"] for c in json.loads(body["result"]["content"][0]["text"])["cards"]}
        assert "SBI Cashback" not in names


# --- Recommendation behaviour ----------------------------------------------

def test_recommend_card_uses_brand_benefits_and_estimates_inr(client, seed):
    key = _create_key(client, seed["alice"])["api_key"]
    out = call_tool(client, key, "recommend_card",
                    {"merchant": "Taj Mahal Palace", "amount_inr": 6000, "category": "hotel"})
    best, second = out["ranking"][0], out["ranking"][1]
    assert best["card_name"] == "Tata Neu Infinity HDFC"
    assert best["reward_rate_percent"] == 10 and best["estimated_reward_inr"] == 600
    assert best["rate_source"] == "brand_ecosystem"
    assert second["card_name"] == "HDFC Diners Club Black"
    assert second["rate_source"] == "campaign" and second["valid_until"]
    assert out["category_detected"] == "travel"


def test_expired_offers_are_excluded(client, seed):
    key = _create_key(client, seed["alice"])["api_key"]
    titles = {o["title"] for o in call_tool(client, key, "get_card_offers", {"merchant": "Croma"})["offers"]}
    assert "Expired Croma deal" not in titles


def test_user_with_no_cards_gets_helpful_message(client, db, seed):
    from app.models import User
    carol = User(email="carol@example.com", name="Carol", auth_provider="google")
    db.add(carol)
    db.commit()
    key = _create_key(client, carol)["api_key"]
    out = call_tool(client, key, "recommend_card", {"merchant": "Croma"})
    assert out["ranking"] == [] and "Add cards" in out["note"]
