"""get_restaurant_offers MCP tool - uses a fake search provider (no network)."""
import asyncio

import pytest

import app.mcp.server as mcp_server
from app.models import PaymentMethod
from app.services.llm_search.base import Platform, RestaurantOffer, SearchResult
from tests.conftest import call_tool, jwt_headers


class FakeProvider:
    provider_name = "fake"

    def __init__(self, delay=0.0, fail=False):
        self.calls = []
        self.delay = delay
        self.fail = fail

    async def search_restaurant_offers(self, restaurant_name, city, platforms=None, parallel=True):
        self.calls.append({"restaurant": restaurant_name, "city": city, "platforms": platforms})
        if self.delay:
            await asyncio.sleep(self.delay)
        if self.fail:
            raise RuntimeError("upstream down")
        return SearchResult(
            restaurant_name=restaurant_name,
            city=city,
            provider="fake",
            summary="Best: 40% off on Swiggy Dineout",
            sources=["https://www.swiggy.com/dineout/x"],
            offers=[
                RestaurantOffer(platform=Platform.SWIGGY_DINEOUT, platform_display_name="Swiggy Dineout",
                                offer_type="pre-booked", discount_text="Flat 40% off on pre-booking",
                                discount_percentage=40),
                RestaurantOffer(platform=Platform.DISTRICT, platform_display_name="District",
                                offer_type="bank_offer", discount_text="Extra 15% off with HDFC credit cards",
                                bank_name="HDFC Bank", max_discount=1000),
                RestaurantOffer(platform=Platform.EAZYDINER, platform_display_name="EazyDiner",
                                offer_type="bank_offer", discount_text="25% off with ICICI cards",
                                bank_name="ICICI Bank"),
            ],
        )


@pytest.fixture
def fake_provider(monkeypatch):
    fp = FakeProvider()
    monkeypatch.setattr(mcp_server, "_get_provider", lambda: fp)
    return fp


def _key(client, user):
    return client.post("/api/mcp-keys", json={"name": "t"}, headers=jwt_headers(user)).json()["api_key"]


def test_returns_dineout_offers_and_flags_offers_on_users_banks(client, seed, fake_provider):
    out = call_tool(client, _key(client, seed["alice"]), "get_restaurant_offers",
                    {"restaurant": "Wok in the Clouds", "city": "Gurgaon"})
    assert len(out["offers"]) == 3
    by_platform = {o["platform"]: o for o in out["offers"]}
    assert by_platform["swiggy_dineout"]["discount_percentage"] == 40
    # Alice holds HDFC cards -> HDFC offer flagged, ICICI not
    assert by_platform["district"]["matches_your_cards"] is True
    assert by_platform["eazydiner"]["matches_your_cards"] is False
    assert out["your_card_banks"] == ["HDFC Bank"]
    # best card to pay with at a restaurant is included for the card UI
    assert out["pay_with"]["card_name"] == "HDFC Diners Club Black"
    # No dine-out apps chosen in PayWise -> search all three
    assert set(out["platforms_searched"]) == {"swiggy_dineout", "eazydiner", "district"}


def test_bank_match_is_per_user(client, seed, fake_provider):
    out = call_tool(client, _key(client, seed["bob"]), "get_restaurant_offers",
                    {"restaurant": "Wok in the Clouds", "city": "Gurgaon"})
    assert out["your_card_banks"] == ["SBI Card"]
    assert not any(o["matches_your_cards"] for o in out["offers"])


def test_uses_users_enabled_dineout_apps(client, db, seed, fake_provider):
    for code in ("swiggy_dineout", "district"):
        db.add(PaymentMethod(user_id=seed["alice"].id, payment_type="dineout_app", nickname=code, is_active=True))
    db.commit()
    out = call_tool(client, _key(client, seed["alice"]), "get_restaurant_offers",
                    {"restaurant": "Bercos", "city": "Delhi"})
    assert set(out["platforms_searched"]) == {"swiggy_dineout", "district"}
    # one independent search per app
    assert sorted(c["platforms"][0].value for c in fake_provider.calls) == ["district", "swiggy_dineout"]
    assert all(len(c["platforms"]) == 1 for c in fake_provider.calls)


def test_explicit_platforms_and_zomato_alias(client, seed, fake_provider):
    out = call_tool(client, _key(client, seed["alice"]), "get_restaurant_offers",
                    {"restaurant": "Bercos", "city": "Delhi", "platforms": ["Zomato", "eazydiner", "bogus"]})
    assert out["platforms_searched"] == ["district", "eazydiner"]


def test_provider_failure_and_timeout_are_reported_per_app(client, seed, monkeypatch):
    key = _key(client, seed["alice"])
    monkeypatch.setattr(mcp_server, "RESTAURANT_RETRY_DELAY_S", 0)
    monkeypatch.setattr(mcp_server, "_get_provider", lambda: FakeProvider(fail=True))
    out = call_tool(client, key, "get_restaurant_offers", {"restaurant": "X", "city": "Delhi"})
    assert out["offers"] == [] and out["complete"] is False
    assert all(s["status"] == "error" and s["attempts"] == 2 for s in out["platform_status"].values())
    assert "search failed" in out["note"]

    monkeypatch.setattr(mcp_server, "RESTAURANT_ATTEMPT_TIMEOUT_S", 0.05)
    monkeypatch.setattr(mcp_server, "RESTAURANT_SEARCH_TIMEOUT_S", 8)
    monkeypatch.setattr(mcp_server, "_get_provider", lambda: FakeProvider(delay=1))
    out = call_tool(client, key, "get_restaurant_offers", {"restaurant": "X", "city": "Delhi"})
    assert {s["status"] for s in out["platform_status"].values()} == {"timed_out"}
    assert "timed out" in out["note"]

    monkeypatch.setattr(mcp_server, "_get_provider", lambda: None)
    out = call_tool(client, key, "get_restaurant_offers", {"restaurant": "X", "city": "Delhi"})
    assert "not configured" in out["note"]


class FlakyEazyDinerProvider(FakeProvider):
    """Reproduces the reported bug: in a combined search EazyDiner's search fails
    (e.g. rate limit), but searched again on its own it finds offers."""

    def __init__(self, eazydiner_failures=1, eazydiner_empty=False):
        super().__init__()
        self.eazydiner_failures = eazydiner_failures
        self.eazydiner_empty = eazydiner_empty

    async def search_restaurant_offers(self, restaurant_name, city, platforms=None, parallel=True):
        if platforms == [Platform.EAZYDINER]:
            self.calls.append({"platforms": platforms})
            if self.eazydiner_failures > 0:
                self.eazydiner_failures -= 1
                raise RuntimeError("429 Too Many Requests")
            if self.eazydiner_empty:
                return SearchResult(restaurant_name=restaurant_name, city=city, offers=[], provider="fake")
            return SearchResult(restaurant_name=restaurant_name, city=city, provider="fake", offers=[
                RestaurantOffer(platform=Platform.EAZYDINER, platform_display_name="EazyDiner",
                                offer_type="bank_offer", discount_text="30% off with HSBC Premier",
                                discount_percentage=30, bank_name="HSBC")])
        return await super().search_restaurant_offers(restaurant_name, city, platforms, parallel)


def test_bug_eazydiner_failure_is_retried_and_recovered(client, seed, monkeypatch):
    fp = FlakyEazyDinerProvider(eazydiner_failures=1)
    monkeypatch.setattr(mcp_server, "_get_provider", lambda: fp)
    monkeypatch.setattr(mcp_server, "RESTAURANT_RETRY_DELAY_S", 0)
    out = call_tool(client, _key(client, seed["alice"]), "get_restaurant_offers",
                    {"restaurant": "Wok in the Clouds", "city": "Gurgaon"})
    st = out["platform_status"]["eazydiner"]
    assert st["status"] == "ok" and st["attempts"] == 2
    assert any(o["platform"] == "eazydiner" and "HSBC" in o["discount_text"] for o in out["offers"])
    assert out["complete"] is True and "note" not in out
    # each app is searched on its own, so one app can't hide another's results
    assert {o["platform"] for o in out["offers"]} == {"swiggy_dineout", "eazydiner", "district"}


def test_bug_eazydiner_persistent_failure_is_reported_not_silent(client, seed, monkeypatch):
    fp = FlakyEazyDinerProvider(eazydiner_failures=5)
    monkeypatch.setattr(mcp_server, "_get_provider", lambda: fp)
    monkeypatch.setattr(mcp_server, "RESTAURANT_RETRY_DELAY_S", 0)
    out = call_tool(client, _key(client, seed["alice"]), "get_restaurant_offers",
                    {"restaurant": "Wok in the Clouds", "city": "Gurgaon"})
    st = out["platform_status"]["eazydiner"]
    assert st["status"] == "error" and st["attempts"] == 2 and "429" in st["error"]
    assert out["platforms_without_results"] == ["eazydiner"] and out["complete"] is False
    assert "EazyDiner: search failed" in out["note"] and "EazyDiner" in out["summary"]
    # other apps' offers still returned
    assert {o["platform"] for o in out["offers"]} == {"swiggy_dineout", "district"}
    assert out["platform_status"]["swiggy_dineout"]["status"] == "ok"


def test_empty_app_is_retried_then_reported_as_no_offers(client, seed, monkeypatch):
    fp = FlakyEazyDinerProvider(eazydiner_failures=0, eazydiner_empty=True)
    monkeypatch.setattr(mcp_server, "_get_provider", lambda: fp)
    monkeypatch.setattr(mcp_server, "RESTAURANT_RETRY_DELAY_S", 0)
    out = call_tool(client, _key(client, seed["alice"]), "get_restaurant_offers",
                    {"restaurant": "Wok in the Clouds", "city": "Gurgaon"})
    assert out["platform_status"]["eazydiner"] == {"status": "no_offers", "offers": 0, "attempts": 2,
                                                  "seconds": out["platform_status"]["eazydiner"]["seconds"]}
    assert "EazyDiner: no offers found" in out["note"]


def test_bank_name_matching():
    t = mcp_server._bank_tokens
    assert t("HDFC Bank") & t("HDFC Bank Credit Cards")
    assert not t("HDFC Bank") & t("Bank of Baroda")      # generic "bank" must not match
    assert t("AMEX") & t("American Express")
    assert t("SBI Card") & t("SBI")
    assert t(None) == set()
