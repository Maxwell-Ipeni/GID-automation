# Get It Done

Amazon Affiliate Product Discovery & Pinterest Publishing Automation.

Discover trending Amazon products, generate affiliate links, and publish to Pinterest from a clean dashboard.

---

## Project Structure

```
backend/        FastAPI application (Python)
frontend/       Next.js dashboard (TypeScript)
convex/         Convex DB schema and functions
docker/         Dockerfiles for backend and frontend
scripts/        Development setup script
```

---

## Setup

### Prerequisites

- Python 3.12+
- Node.js 18+
- Docker & Docker Compose (optional)

### Credentials Required

Before starting, you need:

| Credential | Where to get it |
|------------|----------------|
| Amazon Affiliate Tag | https://affiliate-program.amazon.com |
| Pinterest Access Token | https://developers.pinterest.com |
| Pinterest Board ID | Your Pinterest board URL |

### Option 1: Local Development

```bash
# 1. Run setup script (installs Python deps, Node deps, creates .env)
chmod +x scripts/setup.sh
./scripts/setup.sh

# 2. Configure credentials
# Edit backend/.env and fill in your:
#   - AMAZON_AFFILIATE_TAG
#   - PINTEREST_ACCESS_TOKEN
#   - PINTEREST_BOARD_ID

# 3. Start backend (Terminal 1)
cd backend
source venv/bin/activate
uvicorn main:app --reload --port 8000

# 4. Start frontend (Terminal 2)
cd frontend
npm run dev

# 5. Start Convex (Terminal 3, if using database features)
cd convex
npx convex dev
```

### Option 2: Docker

```bash
docker-compose up
```

### Access the Application

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |

---

## API Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/products` | List discovered products |
| POST | `/api/products/refresh` | Trigger product scrape |
| GET | `/api/trending` | Top trending products |
| GET | `/api/affiliate/{asin}` | Generate affiliate link |
| GET | `/api/pinterest/queue` | Publishing queue |
| POST | `/api/pinterest/queue` | Queue a pin |
| POST | `/api/pinterest/publish` | Publish a queued pin |
| GET | `/api/scraping/status` | Last scrape status |
| POST | `/api/scheduler/scrape` | Start scrape scheduler |
| POST | `/api/scheduler/publish` | Start publish scheduler |
