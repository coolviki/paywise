# PaymentRecommender (PayWise)

A smart payment recommendation app that helps users maximize savings on every purchase by suggesting the best credit card, wallet, or payment method to use.

## Project Structure

```
PaymentRecommender/
├── backend/                    # FastAPI Python backend
│   ├── app/
│   │   ├── api/               # API routes
│   │   ├── core/              # Config, security, database
│   │   ├── models/            # SQLAlchemy models
│   │   ├── schemas/           # Pydantic schemas
│   │   └── services/          # Business logic
│   │       ├── llm_search/    # LLM-powered offer search
│   │       └── scraper/       # Bank website scrapers
│   └── requirements.txt
├── frontend/                   # React + Vite frontend
│   ├── src/
│   │   ├── components/        # React components
│   │   ├── pages/             # Page components
│   │   ├── services/          # API services
│   │   └── types/             # TypeScript types
│   └── package.json
└── CLAUDE.md                   # This file
```

## Key Features

1. **Card Benefits Tracking** - Track cashback/rewards for credit cards at specific brands
2. **Dine-Out Offers** - Real-time offers from Swiggy Dineout, EazyDiner, District
3. **Payment Recommendations** - Suggest best card/wallet for any merchant
4. **Admin Dashboard** - Manage cards, brands, benefits, campaigns

---

## Dine-Out Offers Architecture

### Overview

The app fetches real-time dine-in offers from multiple platforms:
- **Swiggy Dineout** - Pre-booking and walk-in discounts
- **EazyDiner** - Table reservations with discounts
- **District** - Dining offers and bank card deals

### Data Flow

```
User searches "Wok in the Clouds, Delhi"
            │
            ▼
┌─────────────────────────────────────────────────────────┐
│                   LLM Search Service                     │
│  (backend/app/services/llm_search/)                     │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌─────────────────┐  ┌─────────────────┐               │
│  │ Swiggy/EazyDiner│  │    District     │               │
│  │   (LLM Search)  │  │ (Direct Scrape) │               │
│  └────────┬────────┘  └────────┬────────┘               │
│           │                     │                        │
│           ▼                     ▼                        │
│  ┌─────────────────┐  ┌─────────────────┐               │
│  │ Perplexity API  │  │ district_scraper│               │
│  │   or Tavily +   │  │   .py           │               │
│  │   Gemini        │  │ (HTML parsing)  │               │
│  └────────┬────────┘  └────────┬────────┘               │
│           │                     │                        │
│           └──────────┬──────────┘                        │
│                      ▼                                   │
│              Combined Offers                             │
└─────────────────────────────────────────────────────────┘
            │
            ▼
    SSE Stream to Frontend
```

### Why Different Approaches?

| Platform | Method | Reason |
|----------|--------|--------|
| **Swiggy Dineout** | LLM Search (Perplexity/Tavily) | Well-indexed by search engines, LLM can find offers |
| **EazyDiner** | LLM Search (Perplexity/Tavily) | Well-indexed by search engines, LLM can find offers |
| **District** | Direct HTML Scraping | Poorly indexed by search engines, LLM search returns nothing |

### District Scraper Details

**Location:** `backend/app/services/llm_search/district_scraper.py`

**How it works:**
1. Maps city names to District's city codes (e.g., "Delhi" → "ncr")
2. Constructs URL: `district.in/dining/{city}/{restaurant-slug}`
3. Fetches HTML directly from district.in
4. Parses offers using BeautifulSoup:
   - Flat discounts (e.g., "25% OFF", "₹400 OFF")
   - Bank-specific offers (HDFC, ICICI, etc.)
   - Conditions (min spend, valid days)

**URL Pattern:**
```
https://www.district.in/dining/ncr/wok-in-the-clouds-khan-market-new-delhi
                              ▲                    ▲
                           city code          restaurant slug
```

### LLM Search Providers

**Location:** `backend/app/services/llm_search/`

**Providers:**
1. **Perplexity** (`perplexity.py`) - Uses Sonar model with built-in web search
2. **Tavily** (`tavily.py`) - Search API + Gemini for extraction

**Configuration:** Set in `.env`:
```
LLM_SEARCH_PROVIDER=perplexity  # or "tavily"
PERPLEXITY_API_KEY=pplx-xxx
TAVILY_API_KEY=tvly-xxx
GEMINI_API_KEY=xxx  # Required for Tavily
```

### Parallel vs Single Search Mode

Users can toggle between:
- **Thorough (Parallel)** - Makes separate LLM calls for each platform, merges results
- **Quick (Single)** - Single LLM call asking about all platforms at once

Parallel mode is more reliable but slower/costlier.

---

## Card Benefits Scraper

### Overview

Scrapes credit card benefits from bank websites and creates pending changes for admin approval.

**Location:** `backend/app/services/scraper/`

### Supported Banks

| Bank | Scraper | Cards Tracked |
|------|---------|---------------|
| HDFC | `hdfc.py` | Infinia, Regalia, Diners Club, Tata Neu, Swiggy, etc. |
| ICICI | `icici.py` | Amazon Pay, Emeralde, Sapphiro, Coral, etc. |
| SBI | `sbi.py` | SimplyCLICK, Ola Money, BPCL, IRCTC, etc. |

### Data Types Scraped

1. **Benefits** (`ScrapedBenefit`) - Permanent card benefits at specific brands
2. **Campaigns** (`ScrapedCampaign`) - Time-bound promotional offers

### Approval Workflow

```
Scraper finds new benefit
        │
        ▼
Creates PendingEcosystemChange / PendingCampaign
        │
        ▼
Admin reviews in dashboard
        │
        ├── Approve → Creates/updates actual record
        │
        └── Reject → Discarded
```

### Duplicate Card Detection

The scraper includes logic to detect duplicate cards (e.g., "ICICI Coral" vs "ICICI Coral Credit Card"):

```python
# Normalization removes common suffixes
"ICICI Coral Credit Card" → "Coral"
"ICICI Coral" → "Coral"
# These are detected as duplicates
```

**Admin endpoints:**
- `GET /admin/cards/duplicates` - Find duplicate groups
- `POST /admin/cards/merge` - Merge duplicates
- `POST /admin/cards/auto-dedupe` - Auto-merge all duplicates

---

## API Endpoints

### Restaurant Offers

```
POST /api/restaurant-offers
GET  /api/restaurant-offers/stream  # SSE streaming
GET  /api/restaurant-offers/test    # Debug endpoint
```

### Admin

```
# Scraper
POST /admin/scraper/run
GET  /admin/scraper/status

# Pending Changes
GET  /admin/pending
POST /admin/pending/{id}/approve
POST /admin/pending/{id}/reject

# Pending Campaigns
GET  /admin/pending-campaigns
POST /admin/pending-campaigns/{id}/approve

# Duplicate Cards
GET  /admin/cards/duplicates
POST /admin/cards/merge
POST /admin/cards/auto-dedupe
```

---

## Environment Variables

### Backend (.env)

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost/dbname

# Auth
JWT_SECRET_KEY=xxx
GOOGLE_CLIENT_ID=xxx
GOOGLE_CLIENT_SECRET=xxx

# LLM Search
LLM_SEARCH_PROVIDER=perplexity
PERPLEXITY_API_KEY=pplx-xxx
TAVILY_API_KEY=tvly-xxx
GEMINI_API_KEY=xxx

# Optional
REDIS_URL=redis://localhost:6379
```

### Frontend (.env)

```bash
VITE_API_URL=http://localhost:8000
VITE_GOOGLE_CLIENT_ID=xxx
```

---

## Running Locally

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

---

## Deployment

Deployed on Railway:
- Backend: Python FastAPI service
- Frontend: Static site (Vite build)
- Database: PostgreSQL

---

## Future Improvements

1. **Pre-scrape dine-out offers** - Instead of real-time LLM search, periodically scrape all platforms and store in database for faster queries
2. **More platforms** - Add Zomato, Magicpin, etc.
3. **More banks** - Add Axis, Kotak, IDFC scrapers
4. **Push notifications** - Alert users when new offers match their cards
