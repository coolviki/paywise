"""
Seed data for PayWise database.
Run with: python -m app.seed_data
"""

from datetime import date, timedelta
from sqlalchemy.orm import Session
from .core.database import SessionLocal, engine, Base
from .models import Bank, Card, Category, Merchant, MerchantLocation, Offer

# Create all tables
Base.metadata.create_all(bind=engine)


def seed_banks(db: Session):
    """Seed banks data."""
    banks_data = [
        {"name": "HDFC Bank", "code": "hdfc", "logo_url": None},
        {"name": "ICICI Bank", "code": "icici", "logo_url": None},
        {"name": "State Bank of India", "code": "sbi", "logo_url": None},
        {"name": "Axis Bank", "code": "axis", "logo_url": None},
        {"name": "Kotak Mahindra Bank", "code": "kotak", "logo_url": None},
        {"name": "Yes Bank", "code": "yes", "logo_url": None},
        {"name": "IndusInd Bank", "code": "indusind", "logo_url": None},
        {"name": "IDFC First Bank", "code": "idfc", "logo_url": None},
        {"name": "American Express", "code": "amex", "logo_url": None},
        {"name": "Citibank", "code": "citi", "logo_url": None},
        {"name": "RBL Bank", "code": "rbl", "logo_url": None},
        {"name": "AU Small Finance Bank", "code": "au", "logo_url": None},
        {"name": "Federal Bank", "code": "federal", "logo_url": None},
        {"name": "Bank of Baroda", "code": "bob", "logo_url": None},
        {"name": "Standard Chartered", "code": "sc", "logo_url": None},
    ]

    banks = {}
    for data in banks_data:
        existing = db.query(Bank).filter(Bank.code == data["code"]).first()
        if not existing:
            bank = Bank(**data)
            db.add(bank)
            db.flush()
            banks[data["code"]] = bank
        else:
            banks[data["code"]] = existing

    db.commit()
    return banks


def seed_cards(db: Session, banks: dict):
    """Seed cards data."""
    cards_data = [
        # HDFC Cards
        {"bank_code": "hdfc", "name": "HDFC Infinia", "card_type": "credit", "card_network": "visa", "annual_fee": 10000, "reward_type": "points", "base_reward_rate": 3.3},
        {"bank_code": "hdfc", "name": "HDFC Regalia", "card_type": "credit", "card_network": "visa", "annual_fee": 2500, "reward_type": "points", "base_reward_rate": 2.0},
        {"bank_code": "hdfc", "name": "HDFC Diners Club Black", "card_type": "credit", "card_network": "rupay", "annual_fee": 10000, "reward_type": "points", "base_reward_rate": 3.3},
        {"bank_code": "hdfc", "name": "HDFC Millennia", "card_type": "credit", "card_network": "mastercard", "annual_fee": 1000, "reward_type": "cashback", "base_reward_rate": 1.0},
        {"bank_code": "hdfc", "name": "HDFC MoneyBack+", "card_type": "credit", "card_network": "visa", "annual_fee": 500, "reward_type": "cashback", "base_reward_rate": 0.5},

        # ICICI Cards
        {"bank_code": "icici", "name": "ICICI Amazon Pay", "card_type": "credit", "card_network": "visa", "annual_fee": 500, "reward_type": "cashback", "base_reward_rate": 1.0},
        {"bank_code": "icici", "name": "ICICI Sapphiro", "card_type": "credit", "card_network": "visa", "annual_fee": 6500, "reward_type": "points", "base_reward_rate": 2.0},
        {"bank_code": "icici", "name": "ICICI Coral", "card_type": "credit", "card_network": "visa", "annual_fee": 500, "reward_type": "points", "base_reward_rate": 1.0},
        {"bank_code": "icici", "name": "ICICI Emeralde", "card_type": "credit", "card_network": "visa", "annual_fee": 12000, "reward_type": "points", "base_reward_rate": 3.0},

        # Axis Cards
        {"bank_code": "axis", "name": "Axis Flipkart", "card_type": "credit", "card_network": "visa", "annual_fee": 500, "reward_type": "cashback", "base_reward_rate": 1.5},
        {"bank_code": "axis", "name": "Axis Magnus", "card_type": "credit", "card_network": "visa", "annual_fee": 12500, "reward_type": "points", "base_reward_rate": 3.5},
        {"bank_code": "axis", "name": "Axis Reserve", "card_type": "credit", "card_network": "visa", "annual_fee": 50000, "reward_type": "points", "base_reward_rate": 4.0},
        {"bank_code": "axis", "name": "Axis Ace", "card_type": "credit", "card_network": "visa", "annual_fee": 499, "reward_type": "cashback", "base_reward_rate": 2.0},

        # SBI Cards
        {"bank_code": "sbi", "name": "SBI Elite", "card_type": "credit", "card_network": "visa", "annual_fee": 4999, "reward_type": "points", "base_reward_rate": 2.0},
        {"bank_code": "sbi", "name": "SBI Prime", "card_type": "credit", "card_network": "visa", "annual_fee": 2999, "reward_type": "points", "base_reward_rate": 1.5},
        {"bank_code": "sbi", "name": "SBI SimplySAVE", "card_type": "credit", "card_network": "mastercard", "annual_fee": 499, "reward_type": "points", "base_reward_rate": 1.0},
        {"bank_code": "sbi", "name": "SBI BPCL Octane", "card_type": "credit", "card_network": "rupay", "annual_fee": 1499, "reward_type": "cashback", "base_reward_rate": 1.0},

        # Kotak Cards
        {"bank_code": "kotak", "name": "Kotak 811 Dream", "card_type": "credit", "card_network": "visa", "annual_fee": 0, "reward_type": "cashback", "base_reward_rate": 1.0},
        {"bank_code": "kotak", "name": "Kotak Royale Signature", "card_type": "credit", "card_network": "visa", "annual_fee": 2999, "reward_type": "points", "base_reward_rate": 2.0},

        # IDFC Cards
        {"bank_code": "idfc", "name": "IDFC First Select", "card_type": "credit", "card_network": "visa", "annual_fee": 0, "reward_type": "points", "base_reward_rate": 3.0},
        {"bank_code": "idfc", "name": "IDFC First Millennia", "card_type": "credit", "card_network": "visa", "annual_fee": 0, "reward_type": "points", "base_reward_rate": 2.5},

        # Amex Cards
        {"bank_code": "amex", "name": "Amex Platinum", "card_type": "credit", "card_network": "amex", "annual_fee": 60000, "reward_type": "points", "base_reward_rate": 5.0},
        {"bank_code": "amex", "name": "Amex Gold", "card_type": "credit", "card_network": "amex", "annual_fee": 9000, "reward_type": "points", "base_reward_rate": 2.0},
        {"bank_code": "amex", "name": "Amex SmartEarn", "card_type": "credit", "card_network": "amex", "annual_fee": 0, "reward_type": "points", "base_reward_rate": 1.0},

        # Standard Chartered Cards
        {"bank_code": "sc", "name": "SC Ultimate", "card_type": "credit", "card_network": "visa", "annual_fee": 5000, "reward_type": "points", "base_reward_rate": 3.3},
        {"bank_code": "sc", "name": "SC Manhattan", "card_type": "credit", "card_network": "visa", "annual_fee": 999, "reward_type": "cashback", "base_reward_rate": 1.5},
    ]

    cards = {}
    for data in cards_data:
        bank_code = data.pop("bank_code")
        bank = banks.get(bank_code)
        if not bank:
            continue

        existing = db.query(Card).filter(Card.bank_id == bank.id, Card.name == data["name"]).first()
        if not existing:
            card = Card(bank_id=bank.id, **data)
            db.add(card)
            db.flush()
            cards[f"{bank_code}_{data['name']}"] = card
        else:
            cards[f"{bank_code}_{data['name']}"] = existing

    db.commit()
    return cards


def seed_categories(db: Session):
    """Seed categories."""
    categories_data = [
        {"name": "Food & Dining", "icon": "utensils"},
        {"name": "Grocery", "icon": "shopping-cart"},
        {"name": "Shopping", "icon": "shopping-bag"},
        {"name": "Travel", "icon": "plane"},
        {"name": "Entertainment", "icon": "film"},
        {"name": "Fuel", "icon": "fuel"},
        {"name": "Healthcare", "icon": "heart"},
        {"name": "Utilities", "icon": "zap"},
        {"name": "Education", "icon": "book"},
    ]

    categories = {}
    for data in categories_data:
        existing = db.query(Category).filter(Category.name == data["name"]).first()
        if not existing:
            cat = Category(**data)
            db.add(cat)
            db.flush()
            categories[data["name"]] = cat
        else:
            categories[data["name"]] = existing

    db.commit()
    return categories


def seed_merchants(db: Session, categories: dict):
    """Seed merchants and locations."""
    merchants_data = [
        {"name": "Starbucks", "category": "Food & Dining", "is_chain": True},
        {"name": "Domino's Pizza", "category": "Food & Dining", "is_chain": True},
        {"name": "McDonald's", "category": "Food & Dining", "is_chain": True},
        {"name": "Pizza Hut", "category": "Food & Dining", "is_chain": True},
        {"name": "Swiggy", "category": "Food & Dining", "is_chain": False},
        {"name": "Zomato", "category": "Food & Dining", "is_chain": False},
        {"name": "Big Bazaar", "category": "Grocery", "is_chain": True},
        {"name": "DMart", "category": "Grocery", "is_chain": True},
        {"name": "Reliance Fresh", "category": "Grocery", "is_chain": True},
        {"name": "BigBasket", "category": "Grocery", "is_chain": False},
        {"name": "Amazon", "category": "Shopping", "is_chain": False},
        {"name": "Flipkart", "category": "Shopping", "is_chain": False},
        {"name": "Myntra", "category": "Shopping", "is_chain": False},
        {"name": "Lifestyle", "category": "Shopping", "is_chain": True},
        {"name": "Shoppers Stop", "category": "Shopping", "is_chain": True},
        {"name": "MakeMyTrip", "category": "Travel", "is_chain": False},
        {"name": "Yatra", "category": "Travel", "is_chain": False},
        {"name": "Cleartrip", "category": "Travel", "is_chain": False},
        {"name": "BookMyShow", "category": "Entertainment", "is_chain": False},
        {"name": "PVR Cinemas", "category": "Entertainment", "is_chain": True},
        {"name": "INOX", "category": "Entertainment", "is_chain": True},
        {"name": "Indian Oil", "category": "Fuel", "is_chain": True},
        {"name": "HP Petrol", "category": "Fuel", "is_chain": True},
        {"name": "Bharat Petroleum", "category": "Fuel", "is_chain": True},
        {"name": "Apollo Pharmacy", "category": "Healthcare", "is_chain": True},
        {"name": "Medplus", "category": "Healthcare", "is_chain": True},
        {"name": "1mg", "category": "Healthcare", "is_chain": False},
    ]

    merchants = {}
    for data in merchants_data:
        cat_name = data.pop("category")
        category = categories.get(cat_name)

        existing = db.query(Merchant).filter(Merchant.name == data["name"]).first()
        if not existing:
            merchant = Merchant(category_id=category.id if category else None, **data)
            db.add(merchant)
            db.flush()
            merchants[data["name"]] = merchant
        else:
            merchants[data["name"]] = existing

    # Add sample locations for chain merchants
    locations_data = [
        {"merchant": "Starbucks", "address": "Indiranagar 12th Main", "city": "Bangalore", "state": "Karnataka", "latitude": 12.9716, "longitude": 77.6411},
        {"merchant": "Starbucks", "address": "Koramangala 80ft Road", "city": "Bangalore", "state": "Karnataka", "latitude": 12.9352, "longitude": 77.6245},
        {"merchant": "Starbucks", "address": "MG Road", "city": "Bangalore", "state": "Karnataka", "latitude": 12.9758, "longitude": 77.6061},
        {"merchant": "Domino's Pizza", "address": "HSR Layout", "city": "Bangalore", "state": "Karnataka", "latitude": 12.9121, "longitude": 77.6446},
        {"merchant": "Domino's Pizza", "address": "Whitefield", "city": "Bangalore", "state": "Karnataka", "latitude": 12.9698, "longitude": 77.7499},
        {"merchant": "Big Bazaar", "address": "Forum Mall, Koramangala", "city": "Bangalore", "state": "Karnataka", "latitude": 12.9346, "longitude": 77.6119},
        {"merchant": "Big Bazaar", "address": "Phoenix Marketcity", "city": "Bangalore", "state": "Karnataka", "latitude": 12.9977, "longitude": 77.6969},
    ]

    for data in locations_data:
        merchant_name = data.pop("merchant")
        merchant = merchants.get(merchant_name)
        if not merchant:
            continue

        existing = db.query(MerchantLocation).filter(
            MerchantLocation.merchant_id == merchant.id,
            MerchantLocation.address == data["address"]
        ).first()

        if not existing:
            location = MerchantLocation(merchant_id=merchant.id, **data)
            db.add(location)

    db.commit()
    return merchants


def seed_offers(db: Session, banks: dict, merchants: dict):
    """Seed sample offers."""
    today = date.today()
    next_month = today + timedelta(days=30)

    # Get cards
    hdfc_infinia = db.query(Card).join(Bank).filter(Bank.code == "hdfc", Card.name == "HDFC Infinia").first()
    hdfc_regalia = db.query(Card).join(Bank).filter(Bank.code == "hdfc", Card.name == "HDFC Regalia").first()
    icici_amazon = db.query(Card).join(Bank).filter(Bank.code == "icici", Card.name == "ICICI Amazon Pay").first()
    axis_flipkart = db.query(Card).join(Bank).filter(Bank.code == "axis", Card.name == "Axis Flipkart").first()
    sbi_elite = db.query(Card).join(Bank).filter(Bank.code == "sbi", Card.name == "SBI Elite").first()

    offers_data = [
        # Starbucks offers
        {"card": hdfc_infinia, "merchant": "Starbucks", "title": "15% off at Starbucks", "discount_type": "percentage", "discount_value": 15, "min_transaction": 500, "max_discount": 200, "valid_from": today, "valid_until": next_month},
        {"card": hdfc_regalia, "merchant": "Starbucks", "title": "10% off at Starbucks", "discount_type": "percentage", "discount_value": 10, "min_transaction": 300, "max_discount": 150, "valid_from": today, "valid_until": next_month},

        # Swiggy offers
        {"card": hdfc_infinia, "merchant": "Swiggy", "title": "20% off on Swiggy", "discount_type": "percentage", "discount_value": 20, "min_transaction": 500, "max_discount": 100, "valid_from": today, "valid_until": next_month},
        {"card": icici_amazon, "merchant": "Swiggy", "title": "10% cashback on Swiggy", "discount_type": "cashback", "discount_value": 10, "min_transaction": 400, "max_discount": 75, "valid_from": today, "valid_until": next_month},

        # Amazon offers
        {"card": icici_amazon, "merchant": "Amazon", "title": "5% cashback on Amazon", "discount_type": "cashback", "discount_value": 5, "min_transaction": 0, "max_discount": None, "valid_from": today, "valid_until": next_month},
        {"card": hdfc_infinia, "merchant": "Amazon", "title": "10% off on Amazon", "discount_type": "percentage", "discount_value": 10, "min_transaction": 2000, "max_discount": 500, "valid_from": today, "valid_until": next_month},

        # Flipkart offers
        {"card": axis_flipkart, "merchant": "Flipkart", "title": "5% unlimited cashback", "discount_type": "cashback", "discount_value": 5, "min_transaction": 0, "max_discount": None, "valid_from": today, "valid_until": next_month},

        # BookMyShow offers
        {"card": sbi_elite, "merchant": "BookMyShow", "title": "Buy 1 Get 1 Free", "discount_type": "flat", "discount_value": 250, "min_transaction": 250, "max_discount": 250, "valid_from": today, "valid_until": next_month},
        {"card": hdfc_infinia, "merchant": "BookMyShow", "title": "25% off on movie tickets", "discount_type": "percentage", "discount_value": 25, "min_transaction": 200, "max_discount": 200, "valid_from": today, "valid_until": next_month},

        # Fuel offers
        {"card": sbi_elite, "merchant": "Indian Oil", "title": "1% cashback on fuel", "discount_type": "cashback", "discount_value": 1, "min_transaction": 500, "max_discount": 250, "valid_from": today, "valid_until": next_month},
    ]

    for data in offers_data:
        card = data.pop("card")
        merchant_name = data.pop("merchant")
        merchant = merchants.get(merchant_name)

        if not card or not merchant:
            continue

        existing = db.query(Offer).filter(
            Offer.card_id == card.id,
            Offer.merchant_id == merchant.id,
            Offer.title == data["title"]
        ).first()

        if not existing:
            offer = Offer(
                card_id=card.id,
                merchant_id=merchant.id,
                **data
            )
            db.add(offer)

    db.commit()


def seed_all():
    """Run all seed functions."""
    db = SessionLocal()
    try:
        print("Seeding banks...")
        banks = seed_banks(db)
        print(f"Created/found {len(banks)} banks")

        print("Seeding cards...")
        cards = seed_cards(db, banks)
        print(f"Created/found {len(cards)} cards")

        print("Seeding categories...")
        categories = seed_categories(db)
        print(f"Created/found {len(categories)} categories")

        print("Seeding merchants...")
        merchants = seed_merchants(db, categories)
        print(f"Created/found {len(merchants)} merchants")

        print("Seeding offers...")
        seed_offers(db, banks, merchants)
        print("Offers seeded")

        print("Done!")

    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_all()
