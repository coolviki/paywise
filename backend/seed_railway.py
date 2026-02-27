"""
Standalone Railway seed script — no app imports, just psycopg2.
Run from your local machine:

    python backend/seed_railway.py

Make sure psycopg2 is installed: pip install psycopg2-binary
"""

import psycopg2
import psycopg2.extras

DB_URL = "postgresql://postgres:QgwZjRoihepcIJVgoOIRHWvkeelqXcWv@yamanote.proxy.rlwy.net:26258/railway"

conn = psycopg2.connect(DB_URL)
conn.autocommit = False
cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

# ── 1. Tables already created by alembic migrations (UUID-based) ──────────────
# Create campaigns tables if they don't exist (added in 20260226 migration)
print("Checking/creating campaigns tables...")

# campaigns table
cur.execute("""
CREATE TABLE IF NOT EXISTS campaigns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    card_id UUID NOT NULL REFERENCES cards(id) ON DELETE CASCADE,
    brand_id UUID NOT NULL REFERENCES brands(id) ON DELETE CASCADE,
    benefit_rate NUMERIC(5, 2) NOT NULL,
    benefit_type VARCHAR(50) NOT NULL,
    description TEXT,
    terms_url VARCHAR(500),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
)
""")

# Create indexes for campaigns
cur.execute("CREATE INDEX IF NOT EXISTS ix_campaigns_card_id ON campaigns(card_id)")
cur.execute("CREATE INDEX IF NOT EXISTS ix_campaigns_brand_id ON campaigns(brand_id)")
cur.execute("CREATE INDEX IF NOT EXISTS ix_campaigns_dates ON campaigns(start_date, end_date)")

# pending_campaigns table
cur.execute("""
CREATE TABLE IF NOT EXISTS pending_campaigns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    card_id UUID NOT NULL REFERENCES cards(id) ON DELETE CASCADE,
    brand_id UUID NOT NULL REFERENCES brands(id) ON DELETE CASCADE,
    benefit_rate NUMERIC(5, 2) NOT NULL,
    benefit_type VARCHAR(50) NOT NULL,
    description TEXT,
    terms_url VARCHAR(500),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    source_url VARCHAR(500),
    change_type VARCHAR(20) NOT NULL,
    existing_campaign_id UUID REFERENCES campaigns(id) ON DELETE SET NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    scraped_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    reviewed_at TIMESTAMP,
    reviewed_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
)
""")

# Create index for pending_campaigns
cur.execute("CREATE INDEX IF NOT EXISTS ix_pending_campaigns_status ON pending_campaigns(status)")

conn.commit()
print("Campaigns tables ready.")

# ── 2. Seed brands ────────────────────────────────────────────────────────────
# See docs/ECOSYSTEM_BENEFITS.md for documentation
brands_data = [
    # E-Commerce
    ("Tata Group", "tata", "Tata Group retail and consumer properties",
     ["westside", "croma", "bigbasket", "big basket", "zudio", "star bazaar",
      "tata cliq", "tata 1mg", "air asia india", "vistara", "taj hotels", "taj",
      "tata motors", "tata sky", "tatasky", "tanishq", "titan", "starbucks", "tata starbucks"]),
    ("Flipkart", "flipkart", "Flipkart and its subsidiaries",
     ["flipkart", "myntra", "cleartrip"]),
    ("Amazon", "amazon", "Amazon India marketplace and properties",
     ["amazon", "prime video", "amazon fresh", "amazon pay"]),
    ("Reliance Retail", "reliance", "Reliance Retail properties",
     ["reliance", "jiomart", "ajio", "reliance digital", "reliance trends", "netmeds", "reliance fresh"]),
    # Food Delivery
    ("Swiggy", "swiggy", "Swiggy food delivery and Instamart",
     ["swiggy", "instamart", "swiggy dineout", "swiggy genie"]),
    ("Zomato", "zomato", "Zomato food delivery and Blinkit",
     ["zomato", "blinkit", "zomato gold"]),
    # Fuel
    ("Indian Oil", "indianoil", "Indian Oil fuel stations",
     ["indian oil", "indianoil", "iocl"]),
    ("Bharat Petroleum", "bpcl", "BPCL and HP fuel stations",
     ["bharat petroleum", "bpcl", "hp petrol", "hindustan petroleum", "hpcl"]),
    # Travel
    ("MakeMyTrip", "makemytrip", "MakeMyTrip travel bookings",
     ["makemytrip", "mmt", "goibibo"]),
    ("Air India", "airindia", "Air India airlines",
     ["air india", "airindia", "maharaja"]),
    ("IndiGo", "indigo", "IndiGo airlines",
     ["indigo", "6e"]),
    ("EaseMyTrip", "easemytrip", "EaseMyTrip travel bookings",
     ["easemytrip", "ease my trip"]),
    ("ixigo", "ixigo", "ixigo travel platform",
     ["ixigo", "confirmtkt", "abhibus"]),
    # Ride-hailing
    ("Ola", "ola", "Ola cabs and Ola Electric",
     ["ola", "ola cabs", "ola electric", "ola money"]),
    ("Uber", "uber", "Uber ride-hailing",
     ["uber", "uber eats"]),
    # Retail
    ("Shoppers Stop", "shoppersstop", "Shoppers Stop retail",
     ["shoppers stop", "shoppersstop"]),
    # Entertainment
    ("PVR INOX", "pvrinox", "PVR INOX cinemas",
     ["pvr", "inox", "pvr inox", "pvr cinemas"]),
    ("BookMyShow", "bookmyshow", "BookMyShow entertainment ticketing",
     ["bookmyshow", "book my show", "bms"]),
    # Payments
    ("Paytm", "paytm", "Paytm payments and commerce",
     ["paytm", "paytm mall", "paytm money"]),
]

brand_ids = {}
for name, code, desc, keywords in brands_data:
    # Check if brand exists
    cur.execute("SELECT id FROM brands WHERE code = %s", (code,))
    row = cur.fetchone()
    if row:
        brand_id = row[0]
    else:
        cur.execute(
            "INSERT INTO brands (id, name, code, description, is_active, created_at) "
            "VALUES (gen_random_uuid(), %s, %s, %s, true, NOW()) RETURNING id",
            (name, code, desc),
        )
        brand_id = cur.fetchone()[0]
    brand_ids[code] = brand_id

    cur.execute("SELECT keyword FROM brand_keywords WHERE brand_id=%s", (brand_id,))
    existing_kws = {row[0] for row in cur.fetchall()}
    for kw in keywords:
        if kw not in existing_kws:
            cur.execute(
                "INSERT INTO brand_keywords (id, brand_id, keyword, created_at) "
                "VALUES (gen_random_uuid(), %s, %s, NOW())",
                (brand_id, kw),
            )

conn.commit()
print(f"Brands seeded: {list(brand_ids.keys())}")

# ── 2b. Seed missing cards ───────────────────────────────────────────────────
# Cards that may not exist in the database yet
missing_cards = [
    # (name, bank_code, card_type, card_network, annual_fee, reward_type, base_reward_rate)
    ("HDFC Pixel Credit Card", "hdfc", "credit", "visa", 500, "cashback", 5.0),
]

for name, bank_code, card_type, card_network, annual_fee, reward_type, base_reward_rate in missing_cards:
    # Get bank_id
    cur.execute("SELECT id FROM banks WHERE code = %s", (bank_code,))
    row = cur.fetchone()
    if not row:
        print(f"  SKIP (bank not found): {name}")
        continue
    bank_id = row[0]

    # Check if card exists
    cur.execute("SELECT id FROM cards WHERE bank_id = %s AND name = %s", (bank_id, name))
    if cur.fetchone():
        print(f"  EXISTS: {name}")
        continue

    # Insert card
    cur.execute(
        """INSERT INTO cards
               (id, bank_id, name, card_type, card_network, annual_fee, reward_type, base_reward_rate, is_active, created_at)
           VALUES (gen_random_uuid(), %s, %s, %s, %s, %s, %s, %s, true, NOW())""",
        (bank_id, name, card_type, card_network, annual_fee, reward_type, base_reward_rate),
    )
    print(f"  ADDED card: {name}")

conn.commit()

# ── 3. Seed card ecosystem benefits ──────────────────────────────────────────
# Format: (card_name, bank_code, brand_code, benefit_rate, benefit_type, description)
benefits_data = [
    # ========== TATA GROUP ==========
    ("Tata Neu HDFC Bank Credit Card",     "hdfc",  "tata",      5.0,  "neucoins", "5% NeuCoins on Tata properties"),
    ("Tata Neu Plus SBI Card",             "sbi",   "tata",      5.0,  "neucoins", "5% NeuCoins on Tata properties"),
    ("Tata Neu Infinity SBI Card",         "sbi",   "tata",      10.0, "neucoins", "10% NeuCoins on Tata properties"),
    # ========== E-COMMERCE ==========
    ("Flipkart Axis Bank Credit Card",     "axis",  "flipkart",  5.0,  "cashback", "5% on Flipkart, 7.5% on Myntra"),
    ("Amazon Pay ICICI Bank Credit Card",  "icici", "amazon",    5.0,  "cashback", "5% on Amazon (Prime), 3% (non-Prime)"),
    ("Reliance SBI Card PRIME",            "sbi",   "reliance",  10.0, "points",   "10 points per Rs 100 on Ajio & JioMart"),
    # ========== FOOD DELIVERY ==========
    ("Swiggy HDFC Bank Credit Card",       "hdfc",  "swiggy",    10.0, "cashback", "10% on Swiggy (cap Rs 1,500/cycle)"),
    ("Flipkart Axis Bank Credit Card",     "axis",  "swiggy",    4.0,  "cashback", "4% on Swiggy orders"),
    # ========== FUEL ==========
    ("HDFC IndianOil Credit Card",         "hdfc",  "indianoil", 5.0,  "points",   "5% fuel points + surcharge waiver at Indian Oil"),
    ("Axis Bank Indian Oil Credit Card",   "axis",  "indianoil", 4.0,  "points",   "4% fuel points at Indian Oil"),
    ("BPCL Octane SBI Card",               "sbi",   "bpcl",      7.25, "points",   "7.25% value back at BPCL/HP"),
    ("ICICI HPCL Super Saver Credit Card", "icici", "bpcl",      6.5,  "cashback", "6.5% at HP fuel stations"),
    # ========== TRAVEL ==========
    ("MakeMyTrip ICICI Bank Credit Card",  "icici", "makemytrip",6.0,  "mycash",   "6% myCash on hotels, 3% on flights"),
    ("Air India SBI Platinum Credit Card", "sbi",   "airindia",  10.0, "miles",    "10 Maharaja Points per Rs 100 on Air India"),
    ("6E Rewards XL IndiGo HDFC Bank Credit Card", "hdfc", "indigo", 7.0, "bluchips", "7 BluChips per Rs 100 on IndiGo"),
    ("Standard Chartered EaseMyTrip Credit Card", "sc", "easemytrip", 20.0, "discount", "20% off hotels, 10% off flights"),
    ("Ixigo AU Credit Card",               "au",    "ixigo",     10.0, "discount", "10% off flights, hotels, buses via ixigo"),
    # ========== RIDE-HAILING ==========
    ("Ola Money SBI Credit Card",          "sbi",   "ola",       7.0,  "cashback", "7% on Ola rides"),
    ("Flipkart Axis Bank Credit Card",     "axis",  "uber",      4.0,  "cashback", "4% on Uber rides"),
    # ========== RETAIL ==========
    ("HDFC Shoppers Stop Credit Card",     "hdfc",  "shoppersstop", 7.0, "points", "7% value back at Shoppers Stop"),
    # ========== ENTERTAINMENT ==========
    ("PVR Kotak Platinum Credit Card",     "kotak", "pvrinox",   5.0,  "discount", "5% off tickets, 20% off F&B"),
    # ========== PAYMENTS ==========
    ("Paytm HDFC Bank Credit Card",        "hdfc",  "paytm",     3.0,  "cashpoints", "3% cashpoints on Paytm"),
]

inserted = 0
for card_name, bank_code, brand_code, rate, btype, desc in benefits_data:
    cur.execute(
        """SELECT c.id FROM cards c
           JOIN banks b ON b.id = c.bank_id
           WHERE b.code = %s AND c.name = %s""",
        (bank_code, card_name),
    )
    row = cur.fetchone()
    if not row:
        print(f"  SKIP (card not found): {card_name}")
        continue
    card_id = row[0]
    brand_id = brand_ids[brand_code]

    cur.execute(
        "SELECT id FROM card_ecosystem_benefits WHERE card_id=%s AND brand_id=%s",
        (card_id, brand_id),
    )
    if cur.fetchone():
        print(f"  EXISTS: {card_name} → {brand_code}")
        continue

    cur.execute(
        """INSERT INTO card_ecosystem_benefits
               (id, card_id, brand_id, benefit_rate, benefit_type, description, created_at)
           VALUES (gen_random_uuid(), %s, %s, %s, %s, %s, NOW())""",
        (card_id, brand_id, rate, btype, desc),
    )
    inserted += 1
    print(f"  ADDED: {card_name} → {brand_code} ({rate}% {btype})")

conn.commit()
print(f"\nDone! {inserted} ecosystem benefits inserted.")

# ── 4. Verification ───────────────────────────────────────────────────────────
cur.execute("SELECT COUNT(*) FROM brands")
print(f"Brands in DB:                  {cur.fetchone()[0]}")
cur.execute("SELECT COUNT(*) FROM brand_keywords")
print(f"Brand keywords in DB:          {cur.fetchone()[0]}")
cur.execute("SELECT COUNT(*) FROM card_ecosystem_benefits")
print(f"Card ecosystem benefits in DB: {cur.fetchone()[0]}")

cur.close()
conn.close()
