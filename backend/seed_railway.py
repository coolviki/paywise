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
# No need to create tables here - they exist from the migration
print("Using existing tables (created by alembic)...")

# ── 2. Seed brands ────────────────────────────────────────────────────────────
brands_data = [
    ("Tata Group", "tata", "Tata Group retail and consumer properties",
     ["westside", "croma", "bigbasket", "big basket", "zudio", "star bazaar",
      "tata cliq", "tata 1mg", "air asia india", "vistara", "taj hotels", "taj",
      "tata motors", "tata sky", "tatasky"]),
    ("Flipkart", "flipkart", "Flipkart and its subsidiaries",
     ["flipkart", "myntra", "cleartrip"]),
    ("Amazon", "amazon", "Amazon India marketplace and properties",
     ["amazon", "prime video", "amazon fresh"]),
    ("Swiggy", "swiggy", "Swiggy food delivery and Instamart",
     ["swiggy", "instamart"]),
    ("Indian Oil", "indianoil", "Indian Oil fuel stations",
     ["indian oil", "indianoil", "iocl"]),
    ("Bharat Petroleum", "bpcl", "Bharat Petroleum fuel stations",
     ["bharat petroleum", "bpcl", "hp petrol", "hindustan petroleum", "hpcl"]),
    ("Ola", "ola", "Ola cabs and Ola Electric",
     ["ola", "ola cabs", "ola electric", "ola money"]),
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

# ── 3. Seed card ecosystem benefits ──────────────────────────────────────────
benefits_data = [
    ("Tata Neu HDFC Bank Credit Card",     "hdfc",  "tata",      5.0,  "neucoins", "5% NeuCoins on all Tata Group properties"),
    ("Tata Neu Plus SBI Card",             "sbi",   "tata",      5.0,  "neucoins", "5% NeuCoins on all Tata Group properties"),
    ("Tata Neu Infinity SBI Card",         "sbi",   "tata",      10.0, "neucoins", "10% NeuCoins on all Tata Group properties (Infinity tier)"),
    ("Flipkart Axis Bank Credit Card",     "axis",  "flipkart",  5.0,  "cashback", "5% unlimited cashback on Flipkart and Myntra"),
    ("Amazon Pay ICICI Bank Credit Card",  "icici", "amazon",    5.0,  "cashback", "5% cashback on Amazon for Prime members"),
    ("Swiggy HDFC Bank Credit Card",       "hdfc",  "swiggy",    10.0, "cashback", "10% cashback on Swiggy orders"),
    ("HDFC IndianOil Credit Card",         "hdfc",  "indianoil", 5.0,  "points",   "5% fuel points at Indian Oil stations"),
    ("Axis Bank Indian Oil Credit Card",   "axis",  "indianoil", 4.0,  "points",   "4% fuel points at Indian Oil stations"),
    ("BPCL Octane SBI Card",               "sbi",   "bpcl",      7.25, "points",   "7.25% value back at BPCL/HP fuel stations"),
    ("ICICI HPCL Super Saver Credit Card", "icici", "bpcl",      6.5,  "cashback", "6.5% cashback at HP fuel stations"),
    ("Ola Money SBI Credit Card",          "sbi",   "ola",       7.0,  "cashback", "7% cashback on Ola rides and Ola Money transactions"),
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
