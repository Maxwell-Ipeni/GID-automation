# Get It Done

Amazon Affiliate Product Discovery and Pinterest Publishing Automation.

Scrapes trending Amazon products, generates affiliate links, creates AI pin content, and publishes to Pinterest via a dashboard.
## Project Structure

```
backend/        FastAPI application (Python)
frontend/       Next.js dashboard (TypeScript)
convex/         Convex DB schema and functions
docker/         Dockerfiles for backend and frontend
scripts/        Development setup script
## Prerequisites

- Python 3.12+
- Node.js 18+
- Convex account (free tier)
- Pinterest account (for API publishing)

## Setup

### 1. Convex

```bash
npx convex login
npx convex dev
```

The `convex.json` file is in the project root (not in `convex/`). Dashboard at [https://dashboard.convex.dev](https://dashboard.convex.dev).

### 2. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Environment

Copy `backend/.env.example` to `backend/.env` and fill in your values:

```
CONVEX_URL=https://your-project.convex.cloud
AMAZON_AFFILIATE_TAG=your-tag-20
PINTEREST_ACCESS_TOKEN=your-token
PINTEREST_BOARD_ID=your-board-id
```

### 4. Frontend

```bash
cd frontend
npm install
```

Copy `frontend/.env.example` to `frontend/.env.local`:

```
cp frontend/.env.example frontend/.env.local
```

### 5. Run

```bash
# Terminal 1 - Convex
npx convex dev

# Terminal 2 - Backend
cd backend && source venv/bin/activate && uvicorn main:app --reload --port 8000

# Terminal 3 - Frontend
cd frontend && npm run dev
```

### Docker

```bash
docker compose up --build
```

## Access URLs

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| Convex Dashboard | https://dashboard.convex.dev |

## Environment Variables

### Backend (`backend/.env`)

| Variable | Description | Required |
|----------|-------------|----------|
| `CONVEX_URL` | Convex deployment URL | Yes |
| `AMAZON_AFFILIATE_TAG` | Amazon Associates tracking ID | Yes |
| `PINTEREST_APP_ID` | Pinterest app ID | For API |
| `PINTEREST_APP_SECRET` | Pinterest app secret | For API |
| `PINTEREST_ACCESS_TOKEN` | Pinterest API access token | For API |
| `PINTEREST_BOARD_ID` | Pinterest board ID | For API |
| `NVIDIA_API_KEY` | NVIDIA API key for AI content | For AI |
| `BUFFER_API_KEY` | Buffer API key for fallback publishing | For Buffer |
| `SCRAPE_INTERVAL_HOURS` | Scrape frequency (default: 12) | No |
| `PUBLISH_INTERVAL_MINUTES` | Publish frequency in minutes (default: 360) | No |

## Troubleshooting

- Verify `npx convex dev` is running and `CONVEX_URL` matches your deployment.
- Pinterest token must have `pins:write` and `boards:read` scopes. Go to Settings > Test Connection to verify.
- If scraping fails, Amazon may have changed their HTML. Update selectors in `backend/scraping/amazon_scraper.py`.
- If a pin stays queued, check the queue status in the dashboard for error details.

## License

MIT
