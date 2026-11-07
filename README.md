# PayWise - Smart Payment Recommendation App

**Pay Smart. Earn More.**

PayWise helps you choose the best payment method for every purchase by analyzing your credit cards, available offers, and merchant-specific deals.

## Features

- Google Sign-in authentication
- Add and manage multiple credit/debit cards
- Location-based merchant search
- AI-powered payment recommendations
- Real-time offer matching
- **Ask Claude which card to use**: MCP connector for Claude web, desktop and mobile ([details](#use-paywise-from-claude-mcp-connector))
- Dark mode support

## Tech Stack

### Frontend
- React 18 + TypeScript
- Vite
- Tailwind CSS
- Redux Toolkit
- Firebase Auth

### Backend
- Python FastAPI
- PostgreSQL
- SQLAlchemy
- Redis (caching)
- Google Gemini (AI insights in the app)
- MCP Python SDK (Claude connector at `/mcp`)

## Getting Started

### Prerequisites
- Node.js 20+
- Python 3.11+
- PostgreSQL 15+
- Redis

### Development Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/paywise.git
cd paywise
```

2. Set up the backend:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your configuration
```

3. Set up the frontend:
```bash
cd frontend
npm install
cp .env.example .env
# Edit .env with your configuration
```

4. Start with Docker Compose (recommended):
```bash
docker-compose up -d
```

Or start services individually:
```bash
# Terminal 1 - Backend
cd backend
uvicorn app.main:app --reload

# Terminal 2 - Frontend
cd frontend
npm run dev
```

5. Run database migrations:
```bash
cd backend
alembic upgrade head
```

### Environment Variables

#### Backend (.env)
- `DATABASE_URL` - PostgreSQL connection string
- `JWT_SECRET` - Secret key for JWT tokens
- `GOOGLE_PLACES_API_KEY` - Google Places API key
- `ANTHROPIC_API_KEY` - Anthropic API key for Claude
- `FIREBASE_*` - Firebase service account credentials

#### Frontend (.env)
- `VITE_API_URL` - Backend API URL
- `VITE_FIREBASE_*` - Firebase client configuration
- `VITE_GOOGLE_PLACES_API_KEY` - Google Places API key

## Use PayWise from Claude (MCP connector)

PayWise runs a remote [Model Context Protocol](https://modelcontextprotocol.io) (MCP) server, so you can
ask **Claude** which card to use, on the web, in Claude Desktop or **in the Claude mobile app at the
checkout counter**, without opening PayWise. Claude reads your own saved cards, brand benefits and live
offers from PayWise, and PayWise does the reward maths.

<p>
  <img src="docs/screenshots/1_settings.png" width="220" alt="Settings: Connect to Claude">
  <img src="docs/screenshots/2_connect_claude.png" width="220" alt="Connect to Claude page">
  <img src="docs/screenshots/3_new_key_modal.png" width="220" alt="One-time key">
</p>

### Things you can ask Claude
- *"Dinner for 6 at a Taj property tonight, about ₹12,000. Which card?"*
- *"Buying a ₹65k laptop at Croma. Any bank offers on my cards?"*
- *"Which of my cards is best for BigBasket groceries?"*
- *"Going to Wok in the Clouds, Gurgaon tonight. Best Dineout/District deal and which card to pay with?"*
- *"List my cards and their reward rates."*

### Connect in 2 minutes (each user does this once)
1. In PayWise, open **Settings → Integrations → Connect to Claude**.
2. Copy the **connector URL** (`https://<backend>/mcp`).
3. Click **Generate** to create a personal key. **Copy it now; it is shown only once.**
4. On **claude.ai** (web or desktop), go to **Settings → Connectors → Add custom connector**:
   - Name: `PayWise`
   - URL: the connector URL from step 2
   - **Request headers**: `Authorization` = `Bearer pw_live_…`
5. Click **Add**. Enable PayWise from the **+** menu in a chat if it isn't on already.
6. The connector now works in the **Claude mobile app** too (connectors can only be *added* on the web/desktop).

### Tools

All tools are **read-only**. Claude cannot add, change or delete anything in PayWise.

| Tool | Arguments | Returns |
|---|---|---|
| `list_my_cards` | none | Your saved cards: bank, network, reward type, base reward %, annual fee |
| `recommend_card` | `merchant`, `amount_inr?`, `category?` | **All** your cards ranked best-first, with reward %, estimated ₹ reward, rate source (`brand_ecosystem` / `campaign` / `base_rate`), validity date and T&C link |
| `get_card_offers` | `merchant?`, `limit?` | Current (non-expired) bank offers and limited-time campaigns on your cards |
| `find_place` | `query` | Google Places lookup to confirm a merchant and suggest its category |
| `get_restaurant_offers` | `restaurant`, `city`, `platforms?` | **Live dine-out deals** from Swiggy Dineout, EazyDiner and District (Zomato's dining offers now live on District): pre-booked and walk-in discounts plus bank offers, with `matches_your_cards` set when an offer is for a bank you hold. Uses the dine-out apps you enabled in PayWise (all three if none). Live web search, so it takes 10–40 s |

The ranking is deterministic and uses the same logic as the in-app recommendation
(`rank_cards_for_user` in `backend/app/services/recommendation_service.py`). No LLM is called inside
PayWise on this path: Claude explains, PayWise calculates.

### How it works

```
Claude (web / desktop / mobile)
        │  HTTPS, Authorization: Bearer pw_live_…
        ▼
Anthropic cloud ──► https://<backend>/mcp   (FastAPI app, Streamable HTTP, stateless)
                         │
                   McpBearerAuth ── key → user (SHA-256 lookup in mcp_api_keys)
                         │
                   MCP tools ── read only that user's cards, offers, campaigns
                         ▼
                     PostgreSQL
```

Claude connects to the server from Anthropic's cloud, not from your device, so the backend must be
publicly reachable over HTTPS (Railway already provides this).

### Security and privacy
- **Per-user isolation:** the user is resolved from the key on **every request**. **No tool accepts a
  user id or email**, so Claude can't request another user's data even if prompted to.
  This is covered by tests.
- **Keys:** `pw_live_` + 256-bit random value. Only a **SHA-256 hash** is stored. Keys can be revoked
  instantly from the same page (max 5 active per user), and each shows a "last used" time.
- **Separate from app login:** the normal app JWT is **not** accepted on `/mcp`, and an MCP key does not work on `/api`.
- **No card numbers:** PayWise never stores full card numbers, so Claude never sees them.

### Key management API

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/mcp-keys` | List your active keys (never returns the key itself) |
| `POST` | `/api/mcp-keys` | Create a key `{ "name": "My iPhone" }`. The response includes `api_key` **once** |
| `DELETE` | `/api/mcp-keys/{id}` | Revoke a key |

All require the normal app `Authorization: Bearer <JWT>`.

### Local development and testing

```bash
# Run the backend, then try the MCP endpoint with a key generated from the UI
curl -X POST http://localhost:8000/mcp \
  -H "Authorization: Bearer pw_live_..." \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'

# Or explore it interactively with the MCP Inspector
npx @modelcontextprotocol/inspector   # Transport: Streamable HTTP, URL: http://localhost:8000/mcp

# Tests (need PostgreSQL, because the schema uses JSONB)
cd backend
TEST_DATABASE_URL=postgresql://user:pass@localhost/paywise_test pytest tests
```

### Troubleshooting
| Symptom | Likely cause |
|---|---|
| Claude says the connector failed / `401` | Missing `Bearer ` prefix, key copied incompletely, or key revoked. Generate a new one |
| "No cards saved in PayWise yet" | Add cards in **My Cards** first |
| `find_place` returns nothing | `GOOGLE_PLACES_API_KEY` not set on the backend |
| Works on web but not on mobile | Add the connector on claude.ai first; it can't be added from the mobile app |

### Roadmap
- **Phase 2:** OAuth with Google sign-in, so users just click **Connect** instead of copying a key.

## Project Structure

```
paywise/
├── frontend/          # React frontend
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   ├── services/
│   │   └── store/
│   └── ...
├── backend/           # FastAPI backend
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── agents/
│   │   └── mcp/         # Claude MCP connector (server + auth)
│   ├── tests/           # pytest (incl. MCP user-isolation tests)
│   └── ...
├── docs/screenshots/    # UI screenshots
└── docker-compose.yml
```

## API Documentation

Once the backend is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- MCP endpoint (for Claude): http://localhost:8000/mcp (see [Use PayWise from Claude](#use-paywise-from-claude-mcp-connector))

## License

MIT
# Trigger rebuild
