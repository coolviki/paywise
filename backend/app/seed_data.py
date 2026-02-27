"""
Seed data for PayWise database.
Run with: python -m app.seed_data
"""

from datetime import date, timedelta
from sqlalchemy.orm import Session
from .core.database import SessionLocal, engine, Base
from .models import Bank, Card, Category, Merchant, MerchantLocation, Offer, Brand, BrandKeyword, CardEcosystemBenefit

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
        {"name": "RBL Bank", "code": "rbl", "logo_url": None},
        {"name": "AU Small Finance Bank", "code": "au", "logo_url": None},
        {"name": "Federal Bank", "code": "federal", "logo_url": None},
        {"name": "Bank of Baroda", "code": "bob", "logo_url": None},
        {"name": "Standard Chartered", "code": "sc", "logo_url": None},
        {"name": "HSBC", "code": "hsbc", "logo_url": None},
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
    """Seed cards data - comprehensive list of Indian credit cards."""
    cards_data = [
        # ============================================
        # HDFC BANK (18 cards)
        # ============================================
        {"bank_code": "hdfc", "name": "HDFC Infinia Metal Edition", "card_type": "credit", "card_network": "visa", "annual_fee": 12500, "reward_type": "points", "base_reward_rate": 3.33},
        {"bank_code": "hdfc", "name": "HDFC Pixel Credit Card", "card_type": "credit", "card_network": "visa", "annual_fee": 500, "reward_type": "cashback", "base_reward_rate": 5.0},
        {"bank_code": "hdfc", "name": "Paytm HDFC Bank Credit Card", "card_type": "credit", "card_network": "visa", "annual_fee": 499, "reward_type": "cashback", "base_reward_rate": 1.0},
        {"bank_code": "hdfc", "name": "HDFC Diners Club Black Metal Edition", "card_type": "credit", "card_network": "rupay", "annual_fee": 10000, "reward_type": "points", "base_reward_rate": 3.33},
        {"bank_code": "hdfc", "name": "HDFC Diners Club Privilege", "card_type": "credit", "card_network": "rupay", "annual_fee": 2500, "reward_type": "points", "base_reward_rate": 2.67},
        {"bank_code": "hdfc", "name": "HDFC Regalia Gold", "card_type": "credit", "card_network": "visa", "annual_fee": 2500, "reward_type": "points", "base_reward_rate": 2.67},
        {"bank_code": "hdfc", "name": "HDFC Regalia", "card_type": "credit", "card_network": "visa", "annual_fee": 2500, "reward_type": "points", "base_reward_rate": 2.67},
        {"bank_code": "hdfc", "name": "HDFC Diners ClubMiles", "card_type": "credit", "card_network": "rupay", "annual_fee": 1000, "reward_type": "miles", "base_reward_rate": 2.0},
        {"bank_code": "hdfc", "name": "HDFC MoneyBack+", "card_type": "credit", "card_network": "visa", "annual_fee": 500, "reward_type": "cashback", "base_reward_rate": 0.5},
        {"bank_code": "hdfc", "name": "HDFC Millennia", "card_type": "credit", "card_network": "mastercard", "annual_fee": 1000, "reward_type": "cashback", "base_reward_rate": 1.0},
        {"bank_code": "hdfc", "name": "HDFC Freedom", "card_type": "credit", "card_network": "visa", "annual_fee": 500, "reward_type": "points", "base_reward_rate": 0.67},
        {"bank_code": "hdfc", "name": "Swiggy HDFC Bank Credit Card", "card_type": "credit", "card_network": "visa", "annual_fee": 500, "reward_type": "cashback", "base_reward_rate": 1.0},
        {"bank_code": "hdfc", "name": "6E Rewards XL IndiGo HDFC Bank Credit Card", "card_type": "credit", "card_network": "visa", "annual_fee": 1500, "reward_type": "miles", "base_reward_rate": 1.5},
        {"bank_code": "hdfc", "name": "Tata Neu HDFC Bank Credit Card", "card_type": "credit", "card_network": "visa", "annual_fee": 499, "reward_type": "points", "base_reward_rate": 1.5},
        {"bank_code": "hdfc", "name": "HDFC IndianOil Credit Card", "card_type": "credit", "card_network": "visa", "annual_fee": 500, "reward_type": "points", "base_reward_rate": 2.5},
        {"bank_code": "hdfc", "name": "HDFC Shoppers Stop Credit Card", "card_type": "credit", "card_network": "visa", "annual_fee": 500, "reward_type": "points", "base_reward_rate": 1.5},
        {"bank_code": "hdfc", "name": "HDFC UPI RuPay Credit Card", "card_type": "credit", "card_network": "rupay", "annual_fee": 0, "reward_type": "cashback", "base_reward_rate": 1.0},
        {"bank_code": "hdfc", "name": "HDFC Platinum Times Card", "card_type": "credit", "card_network": "visa", "annual_fee": 1000, "reward_type": "points", "base_reward_rate": 1.5},

        # ============================================
        # ICICI BANK (12 cards)
        # ============================================
        {"bank_code": "icici", "name": "ICICI Emeralde Credit Card", "card_type": "credit", "card_network": "mastercard", "annual_fee": 12000, "reward_type": "points", "base_reward_rate": 3.0},
        {"bank_code": "icici", "name": "ICICI Emeralde Private Metal Credit Card", "card_type": "credit", "card_network": "mastercard", "annual_fee": 50000, "reward_type": "points", "base_reward_rate": 3.0},
        {"bank_code": "icici", "name": "ICICI Sapphiro Credit Card", "card_type": "credit", "card_network": "visa", "annual_fee": 6500, "reward_type": "points", "base_reward_rate": 3.0},
        {"bank_code": "icici", "name": "ICICI Rubyx Credit Card", "card_type": "credit", "card_network": "mastercard", "annual_fee": 3000, "reward_type": "points", "base_reward_rate": 2.0},
        {"bank_code": "icici", "name": "ICICI Coral Credit Card", "card_type": "credit", "card_network": "visa", "annual_fee": 500, "reward_type": "points", "base_reward_rate": 2.0},
        {"bank_code": "icici", "name": "ICICI Platinum Chip Credit Card", "card_type": "credit", "card_network": "visa", "annual_fee": 0, "reward_type": "points", "base_reward_rate": 1.0},
        {"bank_code": "icici", "name": "Amazon Pay ICICI Bank Credit Card", "card_type": "credit", "card_network": "visa", "annual_fee": 0, "reward_type": "cashback", "base_reward_rate": 1.0},
        {"bank_code": "icici", "name": "ICICI HPCL Super Saver Credit Card", "card_type": "credit", "card_network": "visa", "annual_fee": 500, "reward_type": "points", "base_reward_rate": 2.5},
        {"bank_code": "icici", "name": "MakeMyTrip ICICI Bank Credit Card", "card_type": "credit", "card_network": "visa", "annual_fee": 500, "reward_type": "points", "base_reward_rate": 2.0},
        {"bank_code": "icici", "name": "Times Black ICICI Bank Credit Card", "card_type": "credit", "card_network": "visa", "annual_fee": 20000, "reward_type": "points", "base_reward_rate": 3.0},
        {"bank_code": "icici", "name": "ICICI Manchester United Credit Card", "card_type": "credit", "card_network": "visa", "annual_fee": 499, "reward_type": "points", "base_reward_rate": 1.0},
        {"bank_code": "icici", "name": "ICICI Ferrari Credit Card", "card_type": "credit", "card_network": "visa", "annual_fee": 1500, "reward_type": "points", "base_reward_rate": 1.5},

        # ============================================
        # SBI CARD (15 cards)
        # ============================================
        {"bank_code": "sbi", "name": "SBI Card ELITE", "card_type": "credit", "card_network": "visa", "annual_fee": 4999, "reward_type": "points", "base_reward_rate": 2.0},
        {"bank_code": "sbi", "name": "Ola Money SBI Credit Card", "card_type": "credit", "card_network": "visa", "annual_fee": 499, "reward_type": "cashback", "base_reward_rate": 1.0},
        {"bank_code": "sbi", "name": "SBI Card PRIME", "card_type": "credit", "card_network": "visa", "annual_fee": 2999, "reward_type": "points", "base_reward_rate": 2.0},
        {"bank_code": "sbi", "name": "SBI Card Pulse", "card_type": "credit", "card_network": "visa", "annual_fee": 1499, "reward_type": "points", "base_reward_rate": 1.5},
        {"bank_code": "sbi", "name": "SimplyCLICK SBI Card", "card_type": "credit", "card_network": "visa", "annual_fee": 499, "reward_type": "points", "base_reward_rate": 0.67},
        {"bank_code": "sbi", "name": "SimplySAVE SBI Card", "card_type": "credit", "card_network": "mastercard", "annual_fee": 499, "reward_type": "points", "base_reward_rate": 0.67},
        {"bank_code": "sbi", "name": "SBI Cashback Credit Card", "card_type": "credit", "card_network": "visa", "annual_fee": 999, "reward_type": "cashback", "base_reward_rate": 1.0},
        {"bank_code": "sbi", "name": "IRCTC SBI Card Premier", "card_type": "credit", "card_network": "visa", "annual_fee": 1499, "reward_type": "points", "base_reward_rate": 2.0},
        {"bank_code": "sbi", "name": "BPCL Octane SBI Card", "card_type": "credit", "card_network": "rupay", "annual_fee": 1499, "reward_type": "points", "base_reward_rate": 2.5},
        {"bank_code": "sbi", "name": "Tata Neu Plus SBI Card", "card_type": "credit", "card_network": "visa", "annual_fee": 499, "reward_type": "points", "base_reward_rate": 1.5},
        {"bank_code": "sbi", "name": "Tata Neu Infinity SBI Card", "card_type": "credit", "card_network": "visa", "annual_fee": 2999, "reward_type": "points", "base_reward_rate": 2.5},
        {"bank_code": "sbi", "name": "Reliance SBI Card PRIME", "card_type": "credit", "card_network": "visa", "annual_fee": 2999, "reward_type": "points", "base_reward_rate": 2.0},
        {"bank_code": "sbi", "name": "Club Vistara SBI Card", "card_type": "credit", "card_network": "visa", "annual_fee": 1499, "reward_type": "miles", "base_reward_rate": 2.0},
        {"bank_code": "sbi", "name": "Air India SBI Platinum Credit Card", "card_type": "credit", "card_network": "visa", "annual_fee": 1499, "reward_type": "miles", "base_reward_rate": 2.0},
        {"bank_code": "sbi", "name": "Fabindia SBI Card", "card_type": "credit", "card_network": "visa", "annual_fee": 499, "reward_type": "points", "base_reward_rate": 1.5},

        # ============================================
        # AXIS BANK (12 cards)
        # ============================================
        {"bank_code": "axis", "name": "Axis Bank Magnus Credit Card", "card_type": "credit", "card_network": "visa", "annual_fee": 12500, "reward_type": "points", "base_reward_rate": 3.0},
        {"bank_code": "axis", "name": "Axis Bank Reserve Credit Card", "card_type": "credit", "card_network": "visa", "annual_fee": 50000, "reward_type": "points", "base_reward_rate": 3.5},
        {"bank_code": "axis", "name": "Axis Bank Atlas Credit Card", "card_type": "credit", "card_network": "visa", "annual_fee": 5000, "reward_type": "miles", "base_reward_rate": 2.5},
        {"bank_code": "axis", "name": "Axis Bank Signature Credit Card", "card_type": "credit", "card_network": "visa", "annual_fee": 3000, "reward_type": "points", "base_reward_rate": 2.5},
        {"bank_code": "axis", "name": "Axis Bank Rewards Credit Card", "card_type": "credit", "card_network": "visa", "annual_fee": 1000, "reward_type": "points", "base_reward_rate": 1.0},
        {"bank_code": "axis", "name": "Axis Bank ACE Credit Card", "card_type": "credit", "card_network": "visa", "annual_fee": 499, "reward_type": "cashback", "base_reward_rate": 2.0},
        {"bank_code": "axis", "name": "Flipkart Axis Bank Credit Card", "card_type": "credit", "card_network": "visa", "annual_fee": 500, "reward_type": "cashback", "base_reward_rate": 1.0},
        {"bank_code": "axis", "name": "Axis Bank MY Zone Credit Card", "card_type": "credit", "card_network": "visa", "annual_fee": 500, "reward_type": "points", "base_reward_rate": 1.0},
        {"bank_code": "axis", "name": "Axis Bank Neo Credit Card", "card_type": "credit", "card_network": "visa", "annual_fee": 250, "reward_type": "cashback", "base_reward_rate": 1.0},
        {"bank_code": "axis", "name": "Axis Bank Select Credit Card", "card_type": "credit", "card_network": "visa", "annual_fee": 0, "reward_type": "points", "base_reward_rate": 1.0},
        {"bank_code": "axis", "name": "Fibe Axis Bank Credit Card", "card_type": "credit", "card_network": "visa", "annual_fee": 0, "reward_type": "cashback", "base_reward_rate": 3.0},
        {"bank_code": "axis", "name": "Airtel Axis Bank Credit Card", "card_type": "credit", "card_network": "visa", "annual_fee": 500, "reward_type": "cashback", "base_reward_rate": 1.0},
        {"bank_code": "axis", "name": "Axis Bank Indian Oil Credit Card", "card_type": "credit", "card_network": "visa", "annual_fee": 500, "reward_type": "points", "base_reward_rate": 4.0},

        # ============================================
        # KOTAK MAHINDRA BANK (10 cards)
        # ============================================
        {"bank_code": "kotak", "name": "Kotak Privy League Signature Credit Card", "card_type": "credit", "card_network": "visa", "annual_fee": 12500, "reward_type": "points", "base_reward_rate": 3.0},
        {"bank_code": "kotak", "name": "Kotak Zen Signature Credit Card", "card_type": "credit", "card_network": "visa", "annual_fee": 1500, "reward_type": "points", "base_reward_rate": 1.67},
        {"bank_code": "kotak", "name": "Kotak Royale Signature Credit Card", "card_type": "credit", "card_network": "visa", "annual_fee": 999, "reward_type": "points", "base_reward_rate": 1.33},
        {"bank_code": "kotak", "name": "Kotak Delight Platinum Credit Card", "card_type": "credit", "card_network": "visa", "annual_fee": 500, "reward_type": "cashback", "base_reward_rate": 1.0},
        {"bank_code": "kotak", "name": "PVR Kotak Platinum Credit Card", "card_type": "credit", "card_network": "visa", "annual_fee": 750, "reward_type": "cashback", "base_reward_rate": 1.5},
        {"bank_code": "kotak", "name": "Kotak Urbane Gold Credit Card", "card_type": "credit", "card_network": "visa", "annual_fee": 199, "reward_type": "points", "base_reward_rate": 0.67},
        {"bank_code": "kotak", "name": "Kotak 811 Credit Card", "card_type": "credit", "card_network": "visa", "annual_fee": 0, "reward_type": "cashback", "base_reward_rate": 1.0},
        {"bank_code": "kotak", "name": "IndiGo Kotak Platinum Credit Card", "card_type": "credit", "card_network": "visa", "annual_fee": 1499, "reward_type": "miles", "base_reward_rate": 2.0},
        {"bank_code": "kotak", "name": "IndiGo Kotak Ka-ching 6E Rewards Credit Card", "card_type": "credit", "card_network": "visa", "annual_fee": 2999, "reward_type": "miles", "base_reward_rate": 2.5},
        {"bank_code": "kotak", "name": "Kotak Fortune Gold Credit Card", "card_type": "credit", "card_network": "visa", "annual_fee": 299, "reward_type": "points", "base_reward_rate": 0.5},

        # ============================================
        # IDFC FIRST BANK (8 cards)
        # ============================================
        {"bank_code": "idfc", "name": "IDFC FIRST Wealth Credit Card", "card_type": "credit", "card_network": "visa", "annual_fee": 0, "reward_type": "points", "base_reward_rate": 1.67},
        {"bank_code": "idfc", "name": "IDFC FIRST Select Credit Card", "card_type": "credit", "card_network": "visa", "annual_fee": 0, "reward_type": "points", "base_reward_rate": 1.67},
        {"bank_code": "idfc", "name": "IDFC FIRST Classic Credit Card", "card_type": "credit", "card_network": "visa", "annual_fee": 0, "reward_type": "points", "base_reward_rate": 0.5},
        {"bank_code": "idfc", "name": "IDFC FIRST Millennia Credit Card", "card_type": "credit", "card_network": "visa", "annual_fee": 0, "reward_type": "points", "base_reward_rate": 0.5},
        {"bank_code": "idfc", "name": "IDFC FIRST WOW Credit Card", "card_type": "credit", "card_network": "rupay", "annual_fee": 0, "reward_type": "points", "base_reward_rate": 0.5},
        {"bank_code": "idfc", "name": "IDFC FIRST SWYP Credit Card", "card_type": "credit", "card_network": "visa", "annual_fee": 0, "reward_type": "points", "base_reward_rate": 1.0},
        {"bank_code": "idfc", "name": "IDFC FIRST Power+ Credit Card", "card_type": "credit", "card_network": "visa", "annual_fee": 499, "reward_type": "points", "base_reward_rate": 2.5},
        {"bank_code": "idfc", "name": "Club Vistara IDFC FIRST Credit Card", "card_type": "credit", "card_network": "visa", "annual_fee": 2500, "reward_type": "miles", "base_reward_rate": 2.0},

        # ============================================
        # AMERICAN EXPRESS (7 cards)
        # ============================================
        {"bank_code": "amex", "name": "American Express Platinum Charge Card", "card_type": "credit", "card_network": "amex", "annual_fee": 66000, "reward_type": "points", "base_reward_rate": 2.5},
        {"bank_code": "amex", "name": "American Express Platinum Reserve Credit Card", "card_type": "credit", "card_network": "amex", "annual_fee": 10000, "reward_type": "points", "base_reward_rate": 2.0},
        {"bank_code": "amex", "name": "American Express Platinum Travel Credit Card", "card_type": "credit", "card_network": "amex", "annual_fee": 5000, "reward_type": "points", "base_reward_rate": 2.0},
        {"bank_code": "amex", "name": "American Express Gold Card", "card_type": "credit", "card_network": "amex", "annual_fee": 9000, "reward_type": "points", "base_reward_rate": 2.0},
        {"bank_code": "amex", "name": "American Express Membership Rewards Credit Card", "card_type": "credit", "card_network": "amex", "annual_fee": 4500, "reward_type": "points", "base_reward_rate": 2.0},
        {"bank_code": "amex", "name": "American Express SmartEarn Credit Card", "card_type": "credit", "card_network": "amex", "annual_fee": 495, "reward_type": "points", "base_reward_rate": 2.0},
        {"bank_code": "amex", "name": "American Express PAYBACK Credit Card", "card_type": "credit", "card_network": "amex", "annual_fee": 0, "reward_type": "points", "base_reward_rate": 1.0},

        # ============================================
        # STANDARD CHARTERED (7 cards)
        # ============================================
        {"bank_code": "sc", "name": "Standard Chartered Ultimate Credit Card", "card_type": "credit", "card_network": "visa", "annual_fee": 5000, "reward_type": "points", "base_reward_rate": 3.33},
        {"bank_code": "sc", "name": "Standard Chartered EaseMyTrip Credit Card", "card_type": "credit", "card_network": "visa", "annual_fee": 2999, "reward_type": "points", "base_reward_rate": 2.0},
        {"bank_code": "sc", "name": "Standard Chartered Rewards Credit Card", "card_type": "credit", "card_network": "visa", "annual_fee": 1000, "reward_type": "points", "base_reward_rate": 2.67},
        {"bank_code": "sc", "name": "Standard Chartered Platinum Rewards Credit Card", "card_type": "credit", "card_network": "visa", "annual_fee": 0, "reward_type": "points", "base_reward_rate": 0.67},
        {"bank_code": "sc", "name": "Standard Chartered Smart Credit Card", "card_type": "credit", "card_network": "visa", "annual_fee": 0, "reward_type": "cashback", "base_reward_rate": 1.0},
        {"bank_code": "sc", "name": "Standard Chartered DigiSmart Credit Card", "card_type": "credit", "card_network": "visa", "annual_fee": 0, "reward_type": "cashback", "base_reward_rate": 1.5},
        {"bank_code": "sc", "name": "Standard Chartered Super Value Titanium Credit Card", "card_type": "credit", "card_network": "mastercard", "annual_fee": 750, "reward_type": "cashback", "base_reward_rate": 1.5},

        # ============================================
        # YES BANK (7 cards)
        # ============================================
        {"bank_code": "yes", "name": "YES Private Credit Card", "card_type": "credit", "card_network": "visa", "annual_fee": 0, "reward_type": "points", "base_reward_rate": 3.0},
        {"bank_code": "yes", "name": "YES RESERV Credit Card", "card_type": "credit", "card_network": "visa", "annual_fee": 10000, "reward_type": "points", "base_reward_rate": 3.0},
        {"bank_code": "yes", "name": "YES Bank ELITE+ Credit Card", "card_type": "credit", "card_network": "visa", "annual_fee": 999, "reward_type": "points", "base_reward_rate": 3.0},
        {"bank_code": "yes", "name": "YES First Credit Card", "card_type": "credit", "card_network": "visa", "annual_fee": 1200, "reward_type": "points", "base_reward_rate": 2.0},
        {"bank_code": "yes", "name": "YES Bank ACE Credit Card", "card_type": "credit", "card_network": "visa", "annual_fee": 1499, "reward_type": "points", "base_reward_rate": 2.0},
        {"bank_code": "yes", "name": "YES Bank Rio Credit Card", "card_type": "credit", "card_network": "rupay", "annual_fee": 0, "reward_type": "points", "base_reward_rate": 1.0},
        {"bank_code": "yes", "name": "YES Bank Klick RuPay Credit Card", "card_type": "credit", "card_network": "rupay", "annual_fee": 0, "reward_type": "cashback", "base_reward_rate": 1.0},

        # ============================================
        # INDUSIND BANK (8 cards)
        # ============================================
        {"bank_code": "indusind", "name": "IndusInd Avios Visa Infinite Credit Card", "card_type": "credit", "card_network": "visa", "annual_fee": 10000, "reward_type": "miles", "base_reward_rate": 3.0},
        {"bank_code": "indusind", "name": "IndusInd Pinnacle World Credit Card", "card_type": "credit", "card_network": "mastercard", "annual_fee": 0, "reward_type": "points", "base_reward_rate": 2.5},
        {"bank_code": "indusind", "name": "IndusInd Legend Credit Card", "card_type": "credit", "card_network": "visa", "annual_fee": 0, "reward_type": "points", "base_reward_rate": 2.0},
        {"bank_code": "indusind", "name": "IndusInd Tiger Credit Card", "card_type": "credit", "card_network": "visa", "annual_fee": 0, "reward_type": "points", "base_reward_rate": 1.5},
        {"bank_code": "indusind", "name": "IndusInd Platinum Aura Edge Credit Card", "card_type": "credit", "card_network": "visa", "annual_fee": 0, "reward_type": "points", "base_reward_rate": 1.5},
        {"bank_code": "indusind", "name": "EazyDiner IndusInd Bank Credit Card", "card_type": "credit", "card_network": "mastercard", "annual_fee": 1999, "reward_type": "cashback", "base_reward_rate": 2.0},
        {"bank_code": "indusind", "name": "IndusInd Nexxt Credit Card", "card_type": "credit", "card_network": "mastercard", "annual_fee": 0, "reward_type": "points", "base_reward_rate": 0.67},
        {"bank_code": "indusind", "name": "British Airways IndusInd Bank Credit Card", "card_type": "credit", "card_network": "visa", "annual_fee": 3000, "reward_type": "miles", "base_reward_rate": 2.0},

        # ============================================
        # RBL BANK (7 cards)
        # ============================================
        {"bank_code": "rbl", "name": "RBL Insignia Preferred Banking World Credit Card", "card_type": "credit", "card_network": "mastercard", "annual_fee": 0, "reward_type": "points", "base_reward_rate": 2.0},
        {"bank_code": "rbl", "name": "RBL Platinum Maxima Credit Card", "card_type": "credit", "card_network": "visa", "annual_fee": 2000, "reward_type": "points", "base_reward_rate": 2.0},
        {"bank_code": "rbl", "name": "RBL Platinum Delight Credit Card", "card_type": "credit", "card_network": "visa", "annual_fee": 1000, "reward_type": "points", "base_reward_rate": 1.5},
        {"bank_code": "rbl", "name": "RBL Titanium Delight Credit Card", "card_type": "credit", "card_network": "visa", "annual_fee": 750, "reward_type": "points", "base_reward_rate": 1.0},
        {"bank_code": "rbl", "name": "RBL ShopRite Credit Card", "card_type": "credit", "card_network": "visa", "annual_fee": 500, "reward_type": "points", "base_reward_rate": 1.0},
        {"bank_code": "rbl", "name": "IndianOil RBL Bank Credit Card", "card_type": "credit", "card_network": "mastercard", "annual_fee": 500, "reward_type": "points", "base_reward_rate": 2.0},
        {"bank_code": "rbl", "name": "Practo Plus RBL Bank Credit Card", "card_type": "credit", "card_network": "mastercard", "annual_fee": 500, "reward_type": "cashback", "base_reward_rate": 1.0},

        # ============================================
        # AU SMALL FINANCE BANK (7 cards)
        # ============================================
        {"bank_code": "au", "name": "AU Bank Zenith Credit Card", "card_type": "credit", "card_network": "visa", "annual_fee": 7999, "reward_type": "points", "base_reward_rate": 5.0},
        {"bank_code": "au", "name": "AU Bank Vetta Credit Card", "card_type": "credit", "card_network": "visa", "annual_fee": 2999, "reward_type": "points", "base_reward_rate": 2.0},
        {"bank_code": "au", "name": "AU Bank Altura Plus Credit Card", "card_type": "credit", "card_network": "visa", "annual_fee": 499, "reward_type": "points", "base_reward_rate": 1.0},
        {"bank_code": "au", "name": "AU Bank Altura Credit Card", "card_type": "credit", "card_network": "visa", "annual_fee": 199, "reward_type": "points", "base_reward_rate": 0.5},
        {"bank_code": "au", "name": "AU Bank LIT Credit Card", "card_type": "credit", "card_network": "visa", "annual_fee": 0, "reward_type": "points", "base_reward_rate": 1.0},
        {"bank_code": "au", "name": "Ixigo AU Credit Card", "card_type": "credit", "card_network": "visa", "annual_fee": 0, "reward_type": "points", "base_reward_rate": 1.25},
        {"bank_code": "au", "name": "AU Bank SwipeUp Credit Card", "card_type": "credit", "card_network": "visa", "annual_fee": 199, "reward_type": "cashback", "base_reward_rate": 1.0},

        # ============================================
        # FEDERAL BANK (5 cards)
        # ============================================
        {"bank_code": "federal", "name": "Federal Bank Visa Celesta Credit Card", "card_type": "credit", "card_network": "visa", "annual_fee": 0, "reward_type": "points", "base_reward_rate": 1.0},
        {"bank_code": "federal", "name": "Federal Bank Mastercard Celesta Credit Card", "card_type": "credit", "card_network": "mastercard", "annual_fee": 0, "reward_type": "points", "base_reward_rate": 1.0},
        {"bank_code": "federal", "name": "Federal Bank Visa Signet Credit Card", "card_type": "credit", "card_network": "visa", "annual_fee": 2500, "reward_type": "points", "base_reward_rate": 1.5},
        {"bank_code": "federal", "name": "Scapia Federal Bank Credit Card", "card_type": "credit", "card_network": "visa", "annual_fee": 0, "reward_type": "points", "base_reward_rate": 1.0},
        {"bank_code": "federal", "name": "OneCard Federal Bank Credit Card", "card_type": "credit", "card_network": "visa", "annual_fee": 0, "reward_type": "cashback", "base_reward_rate": 1.0},

        # ============================================
        # HSBC INDIA (6 cards)
        # ============================================
        {"bank_code": "hsbc", "name": "HSBC Prive Credit Card", "card_type": "credit", "card_network": "mastercard", "annual_fee": 0, "reward_type": "points", "base_reward_rate": 4.0},
        {"bank_code": "hsbc", "name": "HSBC Premier Credit Card", "card_type": "credit", "card_network": "mastercard", "annual_fee": 20000, "reward_type": "points", "base_reward_rate": 2.0},
        {"bank_code": "hsbc", "name": "HSBC TravelOne Credit Card", "card_type": "credit", "card_network": "mastercard", "annual_fee": 4999, "reward_type": "miles", "base_reward_rate": 4.0},
        {"bank_code": "hsbc", "name": "HSBC Live+ Credit Card", "card_type": "credit", "card_network": "visa", "annual_fee": 999, "reward_type": "cashback", "base_reward_rate": 2.5},
        {"bank_code": "hsbc", "name": "HSBC Visa Platinum Credit Card", "card_type": "credit", "card_network": "visa", "annual_fee": 0, "reward_type": "points", "base_reward_rate": 1.0},
        {"bank_code": "hsbc", "name": "HSBC Cashback Credit Card", "card_type": "credit", "card_network": "visa", "annual_fee": 750, "reward_type": "cashback", "base_reward_rate": 1.5},
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


def seed_brands(db: Session, cards: dict):
    """Seed brand ecosystem data — brands, keywords, and card ecosystem benefits."""

    # ------------------------------------------------------------------ brands
    # See docs/ECOSYSTEM_BENEFITS.md for documentation on adding new brands
    brands_data = [
        # E-Commerce
        {
            "name": "Tata Group",
            "code": "tata",
            "description": "Tata Group retail and consumer properties",
            "keywords": [
                "westside", "croma", "bigbasket", "big basket",
                "zudio", "star bazaar", "tata cliq", "tata 1mg",
                "air asia india", "vistara", "taj hotels", "taj",
                "tata motors", "tata sky", "tatasky", "tanishq",
                "titan", "starbucks", "tata starbucks",
            ],
        },
        {
            "name": "Flipkart",
            "code": "flipkart",
            "description": "Flipkart and its subsidiaries",
            "keywords": ["flipkart", "myntra", "cleartrip"],
        },
        {
            "name": "Amazon",
            "code": "amazon",
            "description": "Amazon India marketplace and properties",
            "keywords": ["amazon", "prime video", "amazon fresh", "amazon pay"],
        },
        {
            "name": "Reliance Retail",
            "code": "reliance",
            "description": "Reliance Retail properties",
            "keywords": [
                "reliance", "jiomart", "ajio", "reliance digital",
                "reliance trends", "netmeds", "reliance fresh",
            ],
        },
        # Food Delivery
        {
            "name": "Swiggy",
            "code": "swiggy",
            "description": "Swiggy food delivery and Instamart",
            "keywords": ["swiggy", "instamart", "swiggy dineout", "swiggy genie"],
        },
        {
            "name": "Zomato",
            "code": "zomato",
            "description": "Zomato food delivery and Blinkit",
            "keywords": ["zomato", "blinkit", "zomato gold"],
        },
        # Fuel
        {
            "name": "Indian Oil",
            "code": "indianoil",
            "description": "Indian Oil fuel stations",
            "keywords": ["indian oil", "indianoil", "iocl"],
        },
        {
            "name": "Bharat Petroleum",
            "code": "bpcl",
            "description": "BPCL and HP fuel stations",
            "keywords": ["bharat petroleum", "bpcl", "hp petrol", "hindustan petroleum", "hpcl"],
        },
        # Travel
        {
            "name": "MakeMyTrip",
            "code": "makemytrip",
            "description": "MakeMyTrip travel bookings",
            "keywords": ["makemytrip", "mmt", "goibibo"],
        },
        {
            "name": "Air India",
            "code": "airindia",
            "description": "Air India airlines",
            "keywords": ["air india", "airindia", "maharaja"],
        },
        {
            "name": "IndiGo",
            "code": "indigo",
            "description": "IndiGo airlines",
            "keywords": ["indigo", "6e"],
        },
        {
            "name": "EaseMyTrip",
            "code": "easemytrip",
            "description": "EaseMyTrip travel bookings",
            "keywords": ["easemytrip", "ease my trip"],
        },
        {
            "name": "ixigo",
            "code": "ixigo",
            "description": "ixigo travel platform",
            "keywords": ["ixigo", "confirmtkt", "abhibus"],
        },
        # Ride-hailing
        {
            "name": "Ola",
            "code": "ola",
            "description": "Ola cabs and Ola Electric",
            "keywords": ["ola", "ola cabs", "ola electric", "ola money"],
        },
        {
            "name": "Uber",
            "code": "uber",
            "description": "Uber ride-hailing",
            "keywords": ["uber", "uber eats"],
        },
        # Retail
        {
            "name": "Shoppers Stop",
            "code": "shoppersstop",
            "description": "Shoppers Stop retail",
            "keywords": ["shoppers stop", "shoppersstop"],
        },
        # Entertainment
        {
            "name": "PVR INOX",
            "code": "pvrinox",
            "description": "PVR INOX cinemas",
            "keywords": ["pvr", "inox", "pvr inox", "pvr cinemas"],
        },
        {
            "name": "BookMyShow",
            "code": "bookmyshow",
            "description": "BookMyShow entertainment ticketing",
            "keywords": ["bookmyshow", "book my show", "bms"],
        },
        # Payments
        {
            "name": "Paytm",
            "code": "paytm",
            "description": "Paytm payments and commerce",
            "keywords": ["paytm", "paytm mall", "paytm money"],
        },
    ]

    brands = {}
    for data in brands_data:
        keywords = data.pop("keywords")
        existing = db.query(Brand).filter(Brand.code == data["code"]).first()
        if not existing:
            brand = Brand(**data)
            db.add(brand)
            db.flush()
        else:
            brand = existing
        brands[data["code"]] = brand

        # Upsert keywords
        existing_keywords = {kw.keyword for kw in brand.keywords}
        for kw in keywords:
            if kw not in existing_keywords:
                db.add(BrandKeyword(brand_id=brand.id, keyword=kw))

    db.commit()

    # ------------------------------------------------- card ecosystem benefits
    # See docs/ECOSYSTEM_BENEFITS.md for documentation on adding new benefits
    benefits_data = [
        # ========== TATA GROUP ==========
        {
            "card_name": "Tata Neu HDFC Bank Credit Card",
            "bank_code": "hdfc",
            "brand_code": "tata",
            "benefit_rate": 5.0,
            "benefit_type": "neucoins",
            "description": "5% NeuCoins on Tata properties (Westside, Croma, BigBasket, Taj, Tanishq)",
        },
        {
            "card_name": "Tata Neu Plus SBI Card",
            "bank_code": "sbi",
            "brand_code": "tata",
            "benefit_rate": 5.0,
            "benefit_type": "neucoins",
            "description": "5% NeuCoins on all Tata Group properties",
        },
        {
            "card_name": "Tata Neu Infinity SBI Card",
            "bank_code": "sbi",
            "brand_code": "tata",
            "benefit_rate": 10.0,
            "benefit_type": "neucoins",
            "description": "10% NeuCoins on Tata properties (Infinity tier)",
        },
        # ========== E-COMMERCE ==========
        # Flipkart
        {
            "card_name": "Flipkart Axis Bank Credit Card",
            "bank_code": "axis",
            "brand_code": "flipkart",
            "benefit_rate": 5.0,
            "benefit_type": "cashback",
            "description": "5% cashback on Flipkart, 7.5% on Myntra",
        },
        # Amazon
        {
            "card_name": "Amazon Pay ICICI Bank Credit Card",
            "bank_code": "icici",
            "brand_code": "amazon",
            "benefit_rate": 5.0,
            "benefit_type": "cashback",
            "description": "5% cashback on Amazon (Prime), 3% (non-Prime)",
        },
        # Reliance
        {
            "card_name": "Reliance SBI Card PRIME",
            "bank_code": "sbi",
            "brand_code": "reliance",
            "benefit_rate": 10.0,
            "benefit_type": "points",
            "description": "10 points per Rs 100 on Ajio & JioMart",
        },
        # ========== FOOD DELIVERY ==========
        # Swiggy
        {
            "card_name": "Swiggy HDFC Bank Credit Card",
            "bank_code": "hdfc",
            "brand_code": "swiggy",
            "benefit_rate": 10.0,
            "benefit_type": "cashback",
            "description": "10% cashback on Swiggy (capped Rs 1,500/cycle)",
        },
        # Flipkart Axis also gives 4% on Swiggy
        {
            "card_name": "Flipkart Axis Bank Credit Card",
            "bank_code": "axis",
            "brand_code": "swiggy",
            "benefit_rate": 4.0,
            "benefit_type": "cashback",
            "description": "4% cashback on Swiggy orders",
        },
        # ========== FUEL ==========
        # Indian Oil
        {
            "card_name": "HDFC IndianOil Credit Card",
            "bank_code": "hdfc",
            "brand_code": "indianoil",
            "benefit_rate": 5.0,
            "benefit_type": "points",
            "description": "5% fuel points + 1% surcharge waiver at Indian Oil",
        },
        {
            "card_name": "Axis Bank Indian Oil Credit Card",
            "bank_code": "axis",
            "brand_code": "indianoil",
            "benefit_rate": 4.0,
            "benefit_type": "points",
            "description": "4% fuel points at Indian Oil stations",
        },
        # BPCL/HPCL
        {
            "card_name": "BPCL Octane SBI Card",
            "bank_code": "sbi",
            "brand_code": "bpcl",
            "benefit_rate": 7.25,
            "benefit_type": "points",
            "description": "7.25% value back at BPCL/HP stations",
        },
        {
            "card_name": "ICICI HPCL Super Saver Credit Card",
            "bank_code": "icici",
            "brand_code": "bpcl",
            "benefit_rate": 6.5,
            "benefit_type": "cashback",
            "description": "6.5% cashback at HP fuel stations",
        },
        # ========== TRAVEL ==========
        # MakeMyTrip
        {
            "card_name": "MakeMyTrip ICICI Bank Credit Card",
            "bank_code": "icici",
            "brand_code": "makemytrip",
            "benefit_rate": 6.0,
            "benefit_type": "mycash",
            "description": "6% myCash on hotels, 3% on flights via MakeMyTrip",
        },
        # Air India
        {
            "card_name": "Air India SBI Platinum Credit Card",
            "bank_code": "sbi",
            "brand_code": "airindia",
            "benefit_rate": 10.0,
            "benefit_type": "miles",
            "description": "10 Maharaja Points per Rs 100 on Air India",
        },
        # IndiGo
        {
            "card_name": "6E Rewards XL IndiGo HDFC Bank Credit Card",
            "bank_code": "hdfc",
            "brand_code": "indigo",
            "benefit_rate": 7.0,
            "benefit_type": "bluchips",
            "description": "7 BluChips per Rs 100 on IndiGo bookings",
        },
        # EaseMyTrip
        {
            "card_name": "Standard Chartered EaseMyTrip Credit Card",
            "bank_code": "sc",
            "brand_code": "easemytrip",
            "benefit_rate": 20.0,
            "benefit_type": "discount",
            "description": "20% off hotels, 10% off flights on EaseMyTrip",
        },
        # ixigo
        {
            "card_name": "Ixigo AU Credit Card",
            "bank_code": "au",
            "brand_code": "ixigo",
            "benefit_rate": 10.0,
            "benefit_type": "discount",
            "description": "10% off on flights, hotels, buses via ixigo",
        },
        # ========== RIDE-HAILING ==========
        # Ola
        {
            "card_name": "Ola Money SBI Credit Card",
            "bank_code": "sbi",
            "brand_code": "ola",
            "benefit_rate": 7.0,
            "benefit_type": "cashback",
            "description": "7% cashback on Ola rides",
        },
        # Uber (Flipkart Axis gives 4% on Uber)
        {
            "card_name": "Flipkart Axis Bank Credit Card",
            "bank_code": "axis",
            "brand_code": "uber",
            "benefit_rate": 4.0,
            "benefit_type": "cashback",
            "description": "4% cashback on Uber rides",
        },
        # ========== RETAIL ==========
        # Shoppers Stop
        {
            "card_name": "HDFC Shoppers Stop Credit Card",
            "bank_code": "hdfc",
            "brand_code": "shoppersstop",
            "benefit_rate": 7.0,
            "benefit_type": "points",
            "description": "7% value back at Shoppers Stop (Black variant)",
        },
        # ========== ENTERTAINMENT ==========
        # PVR INOX
        {
            "card_name": "PVR Kotak Platinum Credit Card",
            "bank_code": "kotak",
            "brand_code": "pvrinox",
            "benefit_rate": 5.0,
            "benefit_type": "discount",
            "description": "5% off tickets, 20% off F&B at PVR INOX",
        },
        # ========== PAYMENTS ==========
        # Paytm
        {
            "card_name": "Paytm HDFC Bank Credit Card",
            "bank_code": "hdfc",
            "brand_code": "paytm",
            "benefit_rate": 3.0,
            "benefit_type": "cashpoints",
            "description": "3% cashpoints on Paytm transactions",
        },
    ]

    for data in benefits_data:
        card_name = data.pop("card_name")
        bank_code = data.pop("bank_code")
        brand_code = data.pop("brand_code")

        brand = brands.get(brand_code)
        if not brand:
            continue

        card = db.query(Card).join(Bank).filter(
            Bank.code == bank_code,
            Card.name == card_name,
        ).first()
        if not card:
            continue

        existing = db.query(CardEcosystemBenefit).filter(
            CardEcosystemBenefit.card_id == card.id,
            CardEcosystemBenefit.brand_id == brand.id,
        ).first()

        if not existing:
            db.add(CardEcosystemBenefit(card_id=card.id, brand_id=brand.id, **data))

    db.commit()
    return brands


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

        print("Seeding brands and ecosystem benefits...")
        brands = seed_brands(db, cards)
        print(f"Created/found {len(brands)} brands with keywords and ecosystem benefits")

        print("Done!")

    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_all()
