"""Test fixtures. Needs PostgreSQL (the schema uses JSONB):

    TEST_DATABASE_URL=postgresql://user:pass@localhost/paywise_test pytest
"""
import json
import os
import uuid
from datetime import date, timedelta
from decimal import Decimal

import pytest

TEST_DB = os.environ.get("TEST_DATABASE_URL", "postgresql://pw:pw@localhost/paywise_test")
os.environ["DATABASE_URL"] = TEST_DB  # must be set before the app is imported

from fastapi.testclient import TestClient  # noqa: E402

from app.core.database import Base, SessionLocal, engine  # noqa: E402
from app.core.security import create_access_token  # noqa: E402
from app.main import app  # noqa: E402
from app.models import (  # noqa: E402
    Bank, Brand, BrandKeyword, Campaign, Card, CardEcosystemBenefit, Offer, PaymentMethod, User,
)


@pytest.fixture(autouse=True)
def clean_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:  # runs lifespan -> starts MCP session manager
        yield c


@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    session.close()


def _user(db, email, name):
    u = User(email=email, name=name, auth_provider="google")
    db.add(u)
    db.flush()
    return u


@pytest.fixture
def seed(db):
    return seed_data(db)


def seed_data(db):
    """Two users with different cards. Alice: HDFC Diners Black + Tata Neu Infinity.
    Bob: SBI Cashback only."""
    hdfc = Bank(name="HDFC Bank", code="HDFC")
    sbi = Bank(name="SBI Card", code="SBI")
    db.add_all([hdfc, sbi])
    db.flush()

    diners = Card(bank_id=hdfc.id, name="HDFC Diners Club Black", card_type="credit",
                  reward_type="points", base_reward_rate=Decimal("3.33"), annual_fee=Decimal("10000"))
    neu = Card(bank_id=hdfc.id, name="Tata Neu Infinity HDFC", card_type="credit",
               reward_type="NeuCoins", base_reward_rate=Decimal("1.5"), annual_fee=Decimal("1499"))
    sbi_cb = Card(bank_id=sbi.id, name="SBI Cashback", card_type="credit",
                  reward_type="cashback", base_reward_rate=Decimal("5"), annual_fee=Decimal("999"))
    db.add_all([diners, neu, sbi_cb])
    db.flush()

    taj = Brand(name="Taj Hotels", code="TAJ")
    db.add(taj)
    db.flush()
    db.add(BrandKeyword(brand_id=taj.id, keyword="taj"))
    db.add(CardEcosystemBenefit(card_id=neu.id, brand_id=taj.id, benefit_rate=Decimal("10"),
                                benefit_type="NeuCoins", description="10% NeuCoins at Tata brands",
                                is_active=True))
    db.add(Campaign(card_id=diners.id, brand_id=taj.id, benefit_rate=Decimal("5"),
                    benefit_type="points", description="Diners 5X at Taj",
                    start_date=date.today() - timedelta(days=1),
                    end_date=date.today() + timedelta(days=30), is_active=True))
    db.add(Offer(card_id=sbi_cb.id, title="Flat 10% off at Croma", description="Croma weekend",
                 discount_type="percentage", discount_value=Decimal("10"), is_active=True,
                 valid_until=date.today() + timedelta(days=5)))
    db.add(Offer(card_id=diners.id, title="Rs 1000 off at Croma", description="Croma electronics",
                 discount_type="flat", discount_value=Decimal("1000"), is_active=True,
                 valid_until=date.today() + timedelta(days=5)))
    db.add(Offer(card_id=diners.id, title="Expired Croma deal", discount_type="flat",
                 discount_value=Decimal("500"), is_active=True,
                 valid_until=date.today() - timedelta(days=1)))

    alice = _user(db, "alice@example.com", "Alice")
    bob = _user(db, "bob@example.com", "Bob")
    for user, card, bank in [(alice, diners, hdfc), (alice, neu, hdfc), (bob, sbi_cb, sbi)]:
        db.add(PaymentMethod(user_id=user.id, card_id=card.id, bank_id=bank.id,
                             payment_type="credit_card", is_active=True))
    db.commit()
    return {"alice": alice, "bob": bob}


def jwt_headers(user):
    return {"Authorization": f"Bearer {create_access_token({'sub': str(user.id)})}"}


MCP_HEADERS = {"Accept": "application/json, text/event-stream", "Content-Type": "application/json"}


def mcp_call(client, api_key, method, params=None):
    headers = dict(MCP_HEADERS)
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    body = {"jsonrpc": "2.0", "id": str(uuid.uuid4()), "method": method, "params": params or {}}
    return client.post("/mcp", json=body, headers=headers)


def call_tool(client, api_key, name, arguments=None):
    r = mcp_call(client, api_key, "tools/call", {"name": name, "arguments": arguments or {}})
    assert r.status_code == 200, r.text
    result = r.json()["result"]
    assert not result.get("isError"), result
    if "structuredContent" in result:
        return result["structuredContent"]
    return json.loads(result["content"][0]["text"])
