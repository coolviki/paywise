# PayWise - Smart Payment Recommendation App

**Pay Smart. Earn More.**

PayWise helps you choose the best payment method for every purchase by analyzing your credit cards, available offers, and merchant-specific deals.

## Features

- Google Sign-in authentication
- Add and manage multiple credit/debit cards
- Location-based merchant search
- AI-powered payment recommendations
- Real-time offer matching
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
- Anthropic Claude API (recommendations)

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

PayWise exposes a remote MCP server at `https://<backend>/mcp`, so you can ask Claude
(web, desktop or mobile) *"which card should I use at Croma for ₹65k?"* without opening the app.

**Set up (per user):**
1. In PayWise go to **Settings → Connect to Claude** and generate a personal key (shown once).
2. On claude.ai open **Settings → Connectors → Add custom connector**, paste the URL, and under
   **Request headers** add `Authorization: Bearer pw_live_...`.
3. The connector then also works in the Claude mobile app.

**Tools (all read-only):** `list_my_cards`, `recommend_card`, `get_card_offers`, `find_place`.

**Security model:** the user is resolved from the key on every request (`McpBearerAuth` in
`backend/app/mcp/server.py`). No tool accepts a user id, so a user can only ever see their own
cards. Only a SHA-256 hash of each key is stored; keys can be revoked anytime.

**Tests** (needs PostgreSQL):
```bash
cd backend
TEST_DATABASE_URL=postgresql://user:pass@localhost/paywise_test pytest tests
```

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
│   │   └── agents/
│   └── ...
└── docker-compose.yml
```

## API Documentation

Once the backend is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## License

MIT
# Trigger rebuild
