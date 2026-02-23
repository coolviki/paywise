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

## Pending TODOs (run from laptop)

> **Action required next time you open Claude Code on your laptop:**
>
> Seed the Railway production database with brands, brand keywords, and card ecosystem benefits.
> This is needed for the Tata Neu card recommendation fix to work in production.
>
> ```bash
> pip install psycopg2-binary   # if not already installed
> python backend/seed_railway.py
> ```
>
> The script connects to Railway's Postgres directly and is safe to re-run (skips existing rows).
> File: `backend/seed_railway.py`

---

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
