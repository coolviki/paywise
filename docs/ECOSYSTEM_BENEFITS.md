# Card Ecosystem Benefits - Documentation

This document explains how the card ecosystem benefits system works and how to add new brand partnerships.

## Overview

The ecosystem benefits system allows PayWise to recommend the **best credit card** for a specific merchant by matching:
1. **Merchant name** → **Brand** (via keywords)
2. **Brand** → **Cards with special benefits** (via ecosystem benefits table)

When a user searches for "Westside", the system:
1. Matches "westside" keyword → Tata Group brand
2. Finds cards with Tata ecosystem benefits (e.g., Tata Neu HDFC at 5%)
3. Recommends the card with the highest ecosystem benefit rate

## Database Schema

```
┌──────────────┐       ┌─────────────────────────┐       ┌──────────────┐
│    cards     │       │ card_ecosystem_benefits │       │    brands    │
├──────────────┤       ├─────────────────────────┤       ├──────────────┤
│ id (UUID)    │──────▶│ card_id                 │       │ id (UUID)    │
│ name         │       │ brand_id                │◀──────│ name         │
│ bank_id      │       │ benefit_rate (%)        │       │ code         │
│ base_reward  │       │ benefit_type            │       │ description  │
└──────────────┘       │ description             │       └──────────────┘
                       └─────────────────────────┘              │
                                                                │
                                                        ┌───────┴───────┐
                                                        │ brand_keywords│
                                                        ├───────────────┤
                                                        │ brand_id      │
                                                        │ keyword       │
                                                        └───────────────┘
```

## Current Brands & Benefits (Feb 2026)

### Brands (19 total)

| Category | Brand | Code | Keywords |
|----------|-------|------|----------|
| E-Commerce | Tata Group | `tata` | westside, croma, bigbasket, zudio, taj, tanishq, starbucks |
| E-Commerce | Flipkart | `flipkart` | flipkart, myntra, cleartrip |
| E-Commerce | Amazon | `amazon` | amazon, prime video, amazon fresh |
| E-Commerce | Reliance Retail | `reliance` | jiomart, ajio, reliance digital, netmeds |
| Food Delivery | Swiggy | `swiggy` | swiggy, instamart, swiggy dineout |
| Food Delivery | Zomato | `zomato` | zomato, blinkit |
| Fuel | Indian Oil | `indianoil` | indian oil, indianoil, iocl |
| Fuel | Bharat Petroleum | `bpcl` | bpcl, hp petrol, hindustan petroleum, hpcl |
| Travel | MakeMyTrip | `makemytrip` | makemytrip, mmt, goibibo |
| Travel | Air India | `airindia` | air india, maharaja |
| Travel | IndiGo | `indigo` | indigo, 6e |
| Travel | EaseMyTrip | `easemytrip` | easemytrip |
| Travel | ixigo | `ixigo` | ixigo, confirmtkt, abhibus |
| Ride-hailing | Ola | `ola` | ola, ola cabs, ola electric |
| Ride-hailing | Uber | `uber` | uber, uber eats |
| Retail | Shoppers Stop | `shoppersstop` | shoppers stop |
| Entertainment | PVR INOX | `pvrinox` | pvr, inox |
| Entertainment | BookMyShow | `bookmyshow` | bookmyshow, bms |
| Payments | Paytm | `paytm` | paytm, paytm mall |

### Ecosystem Benefits (22 total)

| Card | Bank | Brand | Rate | Type |
|------|------|-------|------|------|
| Tata Neu HDFC Bank Credit Card | HDFC | Tata | 5% | NeuCoins |
| Tata Neu Plus SBI Card | SBI | Tata | 5% | NeuCoins |
| Tata Neu Infinity SBI Card | SBI | Tata | 10% | NeuCoins |
| Flipkart Axis Bank Credit Card | Axis | Flipkart | 5% | Cashback |
| Flipkart Axis Bank Credit Card | Axis | Swiggy | 4% | Cashback |
| Flipkart Axis Bank Credit Card | Axis | Uber | 4% | Cashback |
| Amazon Pay ICICI Bank Credit Card | ICICI | Amazon | 5% | Cashback |
| Reliance SBI Card PRIME | SBI | Reliance | 10% | Points |
| Swiggy HDFC Bank Credit Card | HDFC | Swiggy | 10% | Cashback |
| HDFC IndianOil Credit Card | HDFC | Indian Oil | 5% | Points |
| Axis Bank Indian Oil Credit Card | Axis | Indian Oil | 4% | Points |
| BPCL Octane SBI Card | SBI | BPCL | 7.25% | Points |
| ICICI HPCL Super Saver Credit Card | ICICI | BPCL | 6.5% | Cashback |
| MakeMyTrip ICICI Bank Credit Card | ICICI | MakeMyTrip | 6% | myCash |
| Air India SBI Platinum Credit Card | SBI | Air India | 10% | Miles |
| 6E Rewards XL IndiGo HDFC Bank Credit Card | HDFC | IndiGo | 7% | BluChips |
| Standard Chartered EaseMyTrip Credit Card | SC | EaseMyTrip | 20% | Discount |
| Ixigo AU Credit Card | AU | ixigo | 10% | Discount |
| Ola Money SBI Credit Card | SBI | Ola | 7% | Cashback |
| HDFC Shoppers Stop Credit Card | HDFC | Shoppers Stop | 7% | Points |
| PVR Kotak Platinum Credit Card | Kotak | PVR INOX | 5% | Discount |
| Paytm HDFC Bank Credit Card | HDFC | Paytm | 3% | Cashpoints |

## How to Add New Brand Partnerships

### Step 1: Research the Partnership

Find the following information:
1. **Card name** (exact name as in our database)
2. **Bank code** (hdfc, icici, sbi, axis, kotak, sc, au, etc.)
3. **Brand/Merchant name**
4. **Benefit rate** (cashback %, reward points multiplier, etc.)
5. **Benefit type** (cashback, points, miles, neucoins, discount, etc.)

### Step 2: Update seed_data.py

Edit `backend/app/seed_data.py`:

#### 2a. Add New Brand (if needed)

Add to `brands_data` list in `seed_brand_ecosystem_data()`:

```python
{
    "name": "Brand Name",
    "code": "brandcode",  # lowercase, no spaces
    "description": "Description of the brand",
    "keywords": ["keyword1", "keyword2", "keyword3"],  # lowercase
},
```

**Keyword Guidelines:**
- Use lowercase only
- Include common variations (e.g., "big basket", "bigbasket")
- Include abbreviations (e.g., "mmt" for MakeMyTrip)
- Include sub-brands (e.g., "myntra" for Flipkart)

#### 2b. Add Ecosystem Benefit

Add to `benefits_data` list:

```python
{
    "card_name": "Exact Card Name",  # Must match cards table
    "bank_code": "bankcode",         # e.g., "hdfc", "icici"
    "brand_code": "brandcode",       # Must match brands_data
    "benefit_rate": 5.0,             # Percentage as float
    "benefit_type": "cashback",      # cashback, points, miles, etc.
    "description": "Brief description of the benefit",
},
```

### Step 3: Update seed_railway.py

Edit `backend/seed_railway.py` with the same data in tuple format:

```python
# In brands_data:
("Brand Name", "brandcode", "Description",
 ["keyword1", "keyword2", "keyword3"]),

# In benefits_data:
("Exact Card Name", "bankcode", "brandcode", 5.0, "cashback", "Description"),
```

### Step 4: Run the Seed Scripts

```bash
# For Railway (production)
python3 backend/seed_railway.py

# For local development
# The seed runs automatically on app startup
```

### Step 5: Verify

Check the output confirms:
- Brand was added/exists
- Keywords were added
- Ecosystem benefit was added

## Benefit Types

| Type | Description | Example |
|------|-------------|---------|
| `cashback` | Direct statement credit | Amazon Pay ICICI (5%) |
| `points` | Reward points | HDFC IndianOil (5%) |
| `neucoins` | Tata NeuCoins (1 = Rs 1) | Tata Neu HDFC (5%) |
| `miles` | Air miles | Air India SBI (10x) |
| `mycash` | MakeMyTrip wallet | MakeMyTrip ICICI (6%) |
| `bluchips` | IndiGo BluChips | IndiGo HDFC (7x) |
| `discount` | Direct discount | EaseMyTrip SC (20%) |
| `cashpoints` | Paytm cashpoints | Paytm HDFC (3%) |

## How the LLM Uses This Data

When generating recommendations, the LLM receives:

```json
{
  "id": "card-uuid",
  "name": "Tata Neu HDFC Bank Credit Card",
  "bank": "HDFC Bank",
  "base_reward_rate": 1.5,
  "ecosystem_benefit_rate": 5.0,  // <-- Injected for matching brands
  "ecosystem_benefit_type": "neucoins",
  "ecosystem_benefit_note": "5% NeuCoins on Tata properties"
}
```

The system prompt tells the LLM:
> "If a card has an `ecosystem_benefit_rate` for this merchant, that rate overrides its `base_reward_rate` — always prefer ecosystem benefits over generic rates."

## Troubleshooting

### Card Not Found
If you see "SKIP (card not found)":
1. Check the exact card name in the cards table
2. Verify the bank_code matches

### Brand Not Matching
If a merchant isn't matching to a brand:
1. Add more keyword variations
2. Check for typos in keywords
3. Keywords are case-insensitive

### Benefit Not Showing
If ecosystem benefit isn't being recommended:
1. Verify the card exists in the user's wallet
2. Check the card_ecosystem_benefits table has the entry
3. Verify the brand_keywords table has matching keywords

## Data Sources for Research

When researching new partnerships:

1. **Official Bank Websites**
   - HDFC: hdfc.com/personal-banking/cards
   - ICICI: icicibank.com/cards
   - SBI: sbicard.com
   - Axis: axisbank.com/retail/cards

2. **Comparison Sites**
   - Paisabazaar.com
   - BankBazaar.com
   - CardInsider.com

3. **Card Review Sites**
   - LiveFromALounge.com
   - CardExpert.in

4. **Official Card Pages**
   - Look for "Benefits", "Rewards", "Partners" sections
   - Check for co-branded card specific pages

## Maintenance Schedule

- **Quarterly Review**: Check for new co-branded cards
- **When Banks Announce**: Add new partnerships immediately
- **User Reports**: If users report missing partnerships, investigate and add

## File Locations

| File | Purpose |
|------|---------|
| `backend/app/seed_data.py` | Main seed data for local development |
| `backend/seed_railway.py` | Standalone seed script for Railway production |
| `backend/app/models/card.py` | CardEcosystemBenefit model |
| `backend/app/models/merchant.py` | Brand and BrandKeyword models |
| `backend/app/services/recommendation_service.py` | Resolves ecosystem benefits |
| `backend/app/agents/recommendation_agent.py` | LLM prompt with benefits |
| `docs/ECOSYSTEM_BENEFITS.md` | This documentation |

---

Last updated: February 2026
