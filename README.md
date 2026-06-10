# Get It Done

Amazon Affiliate Product Discovery and Pinterest Publishing Automation.

Scrapes trending Amazon products, generates affiliate links, creates AI pin content, and publishes to Pinterest via a dashboard.

## Quick Start

```bash
# 1. Install dependencies (one-time)
npm run setup    # or: bash scripts/setup.sh

# 2. Start all services
npm run dev      # starts backend + frontend
npx convex dev   # in a separate terminal
```

Then open http://localhost:3000

## Architecture

| Service | Command | URL |
|---------|---------|-----|
| Frontend (Next.js) | `npm run dev` | http://localhost:3000 |
| Backend (FastAPI) | `npm run dev` | http://localhost:8000 |
| API Docs | - | http://localhost:8000/docs |
| Convex DB | `npx convex dev` | https://dashboard.convex.dev |

## Project Structure

```
backend/        FastAPI application (Python)
frontend/       Next.js dashboard (TypeScript)
convex/         Convex DB schema and functions
docker/         Dockerfiles for backend and frontend
scripts/        Development setup script
```

## Root Scripts

| Script | Description |
|--------|-------------|
| `npm run dev` | Starts backend + frontend concurrently |
| `npm run dev:backend` | Backend only (Python) |
| `npm run setup` | Run setup script |
| `npm run build` | Build frontend for production |
| `npm run start` | Start frontend (production) |
| `npm run lint` | Lint frontend |
| `npm run convex` | Start Convex dev server |

## Prerequisites

- Python 3.12+
- Node.js 18+
- npm
- Convex account (free tier)
- Pinterest account (for API publishing)

## Setup

### 1. Install Dependencies

```bash
npm run setup
```

Or manually:
```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Frontend
cd frontend
npm install
```

### 2. Configure Environment

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local
```

**Required in `backend/.env`:**
```
CONVEX_URL=https://your-project.convex.cloud
AMAZON_AFFILIATE_TAG=your-tag-20
API_KEY=your-super-secret-api-key
```

**Optional (for AI content generation):**
```
NVIDIA_API_KEY=your-nvidia-api-key
```

**Frontend (`frontend/.env.local`):**
```
BACKEND_URL=http://localhost:8000
```

### 3. Start Convex

```bash
npx convex login    # first time only
npx convex dev
```

## Development

### Run Everything

```bash
# Terminal 1: backend + frontend
npm run dev

# Terminal 2: Convex DB
npx convex dev
```

### Run Individual Services

```bash
# Backend only (Python script mode — includes auto-restart on changes)
npm run dev:backend

# Frontend only
cd frontend && npm run dev
```

## Common Tasks

```bash
# Trigger Amazon scraping
curl -X POST http://localhost:8000/api/amazon/scrape

# Trigger auto-queue (publish products to Pinterest)
curl -X POST http://localhost:8000/api/queue/auto \
  -H "X-API-Key: your-api-key"

# Test AI content generation
curl -X POST http://localhost:8000/api/ai/generate-content \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"title":"Wireless Earbuds","category":"electronics","image_url":"https://..."}'

# Test connection to Pinterest
curl http://localhost:8000/api/pinterest/health \
  -H "X-API-Key: your-api-key"
```

## Docker

```bash
docker compose up --build
```

Note: Convex runs externally — ensure `CONVEX_URL` in `backend/.env` points to your Convex deployment.

## Performance

### AI Content Generation
- Vision analysis and LLM call run in parallel (ThreadPoolExecutor)
- Content timeout: 60s | Vision timeout: 5s
- Typical generation time: ~60s per product (down from 130s+ previously)

## Environment Variables

### Backend (`backend/.env`)

| Variable | Description | Required |
|----------|-------------|----------|
| `CONVEX_URL` | Convex deployment URL | Yes |
| `AMAZON_AFFILIATE_TAG` | Amazon Associates tracking ID | Yes |
| `API_KEY` | API authentication key | Yes |
| `NVIDIA_API_KEY` | NVIDIA API key for AI content | For AI features |
| `NVIDIA_API_BASE` | NVIDIA API base URL | No |
| `NVIDIA_MODEL` | NVIDIA model for content | No |
| `NVIDIA_VISION_MODEL` | NVIDIA vision model | No |
| `NVIDIA_FALLBACK_MODEL` | NVIDIA fallback model | No |
| `PINTEREST_APP_ID` | Pinterest app ID | For API |
| `PINTEREST_APP_SECRET` | Pinterest app secret | For API |
| `PINTEREST_ACCESS_TOKEN` | Pinterest API access token | For API |
| `PINTEREST_BOARD_ID` | Pinterest board ID | For API |
| `BUFFER_API_KEY` | Buffer API key for fallback publishing | No |
| `SCRAPE_INTERVAL_HOURS` | Scrape frequency (default: 12) | No |
| `PUBLISH_INTERVAL_MINUTES` | Publish frequency (default: 360) | No |

### Frontend (`frontend/.env.local`)

| Variable | Description | Default |
|----------|-------------|---------|
| `BACKEND_URL` | Backend API URL | http://localhost:8000 |

## Troubleshooting

- Verify `npx convex dev` is running and `CONVEX_URL` matches your deployment.
- Pinterest token must have `pins:write` and `boards:read` scopes. Go to Settings > Test Connection to verify.
- If scraping fails, Amazon may have changed their HTML. Update selectors in `backend/scraping/amazon_scraper.py`.
- If a pin stays queued, check the queue status in the dashboard for error details.
- If AI content generation is slow, see Performance section above.

## License

MIT