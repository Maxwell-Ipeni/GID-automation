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

## Project Architecture

```
Amazon Scraping (Backend)
        ↓
Convex DB (Products, Affiliate Links, Pinterest Posts)
        ↓
Next.js Frontend (Dashboard UI)
        ↓
Pinterest API (Real Pin Publishing)
```

- **Backend**: Python FastAPI - handles scraping, scheduling, and Convex integration
- **Frontend**: Next.js 14 - displays data and provides controls
- **Convex**: Backend-as-a-Service - stores products, affiliate links, and Pinterest queue
- **Pinterest API**: Real pin publishing with scheduling and retry

---

## Features

### Phase 1 - MVP (Complete)

- [x] Amazon Best Sellers scraping
- [x] Amazon Movers & Shakers scraping  
- [x] Amazon New Releases scraping
- [x] Amazon Deals scraping
- [x] Product trend scoring (weighted algorithm)
- [x] Affiliate link generation with Amazon tag
- [x] Pinterest post queueing
- [x] Dashboard with real-time stats
- [x] Products grid with filtering
- [x] Queue management UI with tabs

### Phase 2 - Pinterest API (Complete)

- [x] Real Pinterest API integration
- [x] Scheduled pin publishing (15-45 min delays)
- [x] Automatic retry on failure (1 retry, then manual)
- [x] Connection testing via Settings UI
- [x] Board listing and selection
- [x] Optimized pin titles and descriptions
- [x] Affiliate link in Pinterest link field

### Phase 3 - Future

- [ ] AI-powered pin content generation
- [ ] Click tracking for affiliate links
- [ ] Email/push notifications
- [ ] Multi-board publishing
- [ ] Analytics dashboard

---

## Prerequisites

- Python 3.12+
- Node.js 18+
- Convex account (free tier available)
- Pinterest account (for API access)

---

## Complete Setup Guide

### Step 1: Convex Setup

1. **Login to Convex**:
   ```bash
   cd /home/mg/Projects/GID && npx convex login
   ```

2. **Run Convex dev server**:
   ```bash
   cd /home/mg/Projects/GID && npx convex dev
   ```
   
   The `convex.json` file is in the project root, NOT in the `convex/` subdirectory.

3. **Verify**: Dashboard at `https://dashboard.convex.dev`

### Step 2: Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Pinterest API Setup

#### 3.1 Create Pinterest App

1. Go to https://developers.pinterest.com/
2. Click **"Connect"** and log in
3. Click **"My Apps"** → **"Create app"**
4. Fill in:
   - **App name:** `Get It Done`
   - **Description:** `Amazon affiliate automation`
   - **Website URL:** `https://getitdone.app` (or any URL)
5. Click **Create**
6. Copy your **App ID** and **App Secret**

#### 3.2 Get Access Token

**Option A: Generate Token (Easiest)**
1. In your app dashboard, click **"Auth"** or **"Generate token"**
2. Select scopes: `pins:write`, `boards:read`
3. Click **Generate token**
4. Copy the token (starts with `ATM`)

**Option B: OAuth Flow**
1. Build OAuth URL with your app credentials
2. User authorizes your app
3. Exchange code for access token

#### 3.3 Get Board ID

**Method A: Use Settings UI (Easiest)**
1. Start the backend and frontend
2. Go to Settings page
3. Enter Pinterest credentials
4. Click "Test Connection"
5. Your boards will appear - click to select

**Method B: Manual**
1. Go to your Pinterest board
2. Open browser DevTools (F12)
3. Search for `"boardId"` or `"data-board-id"` in HTML
4. Copy the numeric ID

#### 3.4 Configure Backend

Edit `backend/.env`:
```bash
PINTEREST_APP_ID=1234567890123
PINTEREST_APP_SECRET=your-app-secret
PINTEREST_ACCESS_TOKEN=ATMxxxxxxxxxxxxx
PINTEREST_BOARD_ID=1234567890123
```

### Step 4: Start the Application

**Terminal 1 - Convex:**
```bash
cd /home/mg/Projects/GID && npx convex dev
```

**Terminal 2 - Backend:**
```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload --port 8000
```

**Terminal 3 - Frontend:**
```bash
cd frontend
npm run dev
```

### Access URLs

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| Convex Dashboard | https://dashboard.convex.dev |

---

## API Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/stats` | Dashboard statistics |
| GET | `/api/products` | List discovered products |
| GET | `/api/trending` | Top trending products |
| GET | `/api/affiliate/{asin}` | Generate affiliate link |
| GET | `/api/pinterest/queue` | Publishing queue |
| POST | `/api/pinterest/queue` | Queue a pin |
| POST | `/api/pinterest/test` | Test Pinterest connection |
| GET | `/api/pinterest/boards` | List Pinterest boards |
| GET | `/api/pinterest/status` | Pinterest connection status |
| POST | `/api/scheduler/scrape` | Trigger scraping job |
| POST | `/api/scheduler/publish` | Trigger publishing job |
| GET | `/api/scraping/status` | Recent scraping logs |

---

## Environment Variables

### Backend (.env)

| Variable | Description | Required |
|----------|-------------|----------|
| `CONVEX_URL` | Convex deployment URL | ✓ |
| `AMAZON_AFFILIATE_TAG` | Amazon Associates tracking ID (e.g., `yourname-20`) | ✓ |
| `PINTEREST_APP_ID` | Pinterest app ID | ✓ (for API) |
| `PINTEREST_APP_SECRET` | Pinterest app secret | ✓ (for API) |
| `PINTEREST_ACCESS_TOKEN` | Pinterest API access token | ✓ (for API) |
| `PINTEREST_BOARD_ID` | Pinterest board ID for publishing | ✓ (for API) |
| `SCRAPE_INTERVAL_HOURS` | Scrape frequency (default: 4) | Optional |
| `PUBLISH_DELAY_MIN_MINUTES` | Min delay between pins (default: 15) | Optional |
| `PUBLISH_DELAY_MAX_MINUTES` | Max delay between pins (default: 45) | Optional |
| `PUBLISH_RETRY_ATTEMPTS` | Auto-retry count (default: 1) | Optional |

---

## Pinterest API Reference

### Endpoints Used

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/v5/pins` | POST | Create a new pin |
| `/v5/boards` | GET | List user's boards |

### Pin Creation Request

```json
{
  "board_id": "123456789",
  "title": "Product Name - ⭐4.5/5 | $29.99",
  "description": "Check out this product on Amazon!\n\n⭐ 4.5 star rating\n📝 1.2K customer reviews\n💰 $29.99\n\nLink in bio 🔗\n\n#affiliate #amazonfinds",
  "link": "https://amazon.com/dp/B0XXXXX/?tag=your-tag-20",
  "media": {
    "source_type": "image_url",
    "url": "https://product-image.jpg"
  },
  "scheduled_at": "1699900800"
}
```

### Rate Limits

| Action | Limit |
|--------|-------|
| Create pin | ~500/day |
| Get boards | 300/min |

---

## Troubleshooting

### Convex Connection Issues

1. Check that `npx convex dev` is running
2. Verify `CONVEX_URL` in `backend/.env` matches your deployment
3. Check `.env.local` was created with correct deployment URL

### Pinterest Connection Issues

1. Verify `PINTEREST_ACCESS_TOKEN` is valid (not expired)
2. Check `PINTEREST_BOARD_ID` is correct (numeric ID, not username/slug)
3. Ensure token has `pins:write` and `boards:read` permissions
4. Go to Settings → Test Connection for diagnostics

### Scraping Issues

Amazon frequently changes their HTML. If scraping fails:
1. Check Amazon directly in browser
2. Update selectors in `backend/scraping/amazon_scraper.py`
3. Try a different source (bestsellers, movers, new_releases, deals)

### Pin Not Publishing

1. Check Pinterest queue in UI - is status "queued" or "failed"?
2. If "failed", check error message
3. Verify Pinterest credentials in Settings
4. Click "Test Connection" to diagnose

---

## Pinterest Developer Resources

| Resource | Link |
|----------|------|
| Developer Portal | https://developers.pinterest.com |
| API Docs | https://developers.pinterest.com/docs |
| Create App | https://developers.pinterest.com/apps/create/ |
| API Reference | https://developers.pinterest.com/docs/api/v5 |

---

## License

MIT