#!/usr/bin/env python
"""
Get It Done - Amazon Affiliate Pinterest Automation System
Main entry point for the FastAPI application.
"""

import asyncio
import concurrent.futures
import logging
import os
import time
from contextlib import asynccontextmanager
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, HTTPException, Query, Depends, status as http_status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from scraping.amazon_scraper import AmazonScraper
from affiliate.affiliate_engine import AffiliateEngine
from pinterest.pinterest_publisher import PinterestPublisher
from pinterest.pinterest_trends import PinterestTrendService
from scoring.product_scorer import ProductScorer
from scheduler.scraper_scheduler import ScraperScheduler
from trends.google_trends import AmazonTrendService
from utils.config import get_settings
from utils.convex_client import ConvexService
from utils.state import get_state
from ai.pin_writer import PinContentAI
from images.image_generator import PinImageGenerator

settings = get_settings()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

# ─── Security ──────────────────────────────────────────────────────────
security = HTTPBearer(auto_error=False)


async def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    expected = settings.API_KEY
    if not expected:
        return "no-auth"
    if not credentials or credentials.credentials != expected:
        raise HTTPException(
            status_code=http_status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials


# ─── Rate-limiting (in-memory sliding window) ──────────────────────────
_rate_limit_window: Dict[str, List[float]] = {}


def check_rate_limit(key: str, max_requests: int, window_seconds: int) -> Dict[str, Any]:
    now = time.time()
    window = _rate_limit_window.setdefault(key, [])
    window[:] = [ts for ts in window if now - ts <= window_seconds]
    remaining = max_requests - len(window)
    if remaining <= 0:
        return {"allowed": False, "remaining": 0}
    window.append(now)
    return {"allowed": True, "remaining": remaining - 1}


# ─── Service factories (request-scoped) ────────────────────────────────
def get_scraper() -> AmazonScraper:
    return AmazonScraper()


def get_affiliate_engine() -> AffiliateEngine:
    return AffiliateEngine(tag=settings.AMAZON_AFFILIATE_TAG)


def get_pinterest() -> PinterestPublisher:
    return PinterestPublisher(
        access_token=settings.PINTEREST_ACCESS_TOKEN,
        board_id=settings.PINTEREST_BOARD_ID,
    )


def get_convex() -> ConvexService:
    return ConvexService()


def get_content_ai() -> PinContentAI:
    return PinContentAI()


def get_image_gen() -> PinImageGenerator:
    return PinImageGenerator()


# ─── Static files directory ───────────────────────────────────────────
os.makedirs(settings.PIN_IMAGE_DIR, exist_ok=True)


# ─── Schedule state (in-memory, persisted via Convex) ──────────────────
_schedule_state: dict = {
    "scrape": {"last_run": None, "next_run": None},
    "publish": {"last_run": None, "next_run": None},
    "trends": {"last_run": None, "next_run": None},
}


async def _load_schedule_state() -> None:
    convex = get_convex()
    try:
        last_scrape = await convex.settings_get("last_scrape_at")
        last_publish = await convex.settings_get("last_publish_at")
        now = time.time()

        if last_scrape is not None:
            _schedule_state["scrape"]["last_run"] = int(last_scrape)
            nxt = int(last_scrape) + settings.SCRAPE_INTERVAL_HOURS * 3600
            _schedule_state["scrape"]["next_run"] = int(max(nxt, now))
        else:
            _schedule_state["scrape"]["next_run"] = int(now + 15)

        if last_publish is not None:
            _schedule_state["publish"]["last_run"] = int(last_publish)
            nxt = int(last_publish) + settings.PUBLISH_INTERVAL_MINUTES * 60
            _schedule_state["publish"]["next_run"] = int(max(nxt, now))
        else:
            _schedule_state["publish"]["next_run"] = int(now + 30)

        last_trends = await convex.settings_get("last_trends_at")
        if last_trends is not None:
            _schedule_state["trends"]["last_run"] = int(last_trends)
            nxt = int(last_trends) + settings.SCRAPE_INTERVAL_HOURS * 1800
            _schedule_state["trends"]["next_run"] = int(max(nxt, now))
        else:
            _schedule_state["trends"]["next_run"] = int(now + 60)

        logger.info(
            "Schedule state loaded — scrape next: %s, publish next: %s, trends next: %s",
            _fmt_ts(_schedule_state["scrape"]["next_run"]),
            _fmt_ts(_schedule_state["publish"]["next_run"]),
            _fmt_ts(_schedule_state["trends"]["next_run"]),
        )
    except Exception as e:
        logger.warning("Could not load schedule state from Convex: %s", e)
        _schedule_state["scrape"]["next_run"] = int(time.time() + 15)
        _schedule_state["publish"]["next_run"] = int(time.time() + 30)
        _schedule_state["trends"]["next_run"] = int(time.time() + 60)


async def _save_schedule_state(component: str) -> None:
    convex = get_convex()
    try:
        ts = int(time.time())
        key = f"last_{component}_at"
        await convex.settings_set(key, ts)
        _schedule_state[component]["last_run"] = ts
    except Exception as e:
        logger.warning("Failed to save %s schedule state: %s", component, e)


def _fmt_ts(ts: Optional[int]) -> str:
    if ts is None:
        return ""
    from datetime import datetime
    return datetime.fromtimestamp(ts).isoformat()


async def scheduled_trends_sync():
    logger.info("Scheduled trends sync triggered")
    results: Dict[str, Any] = {}
    try:
        pinterest_service = PinterestTrendService()
        pinterest_results = await pinterest_service.run_all_regions(timeframe="today")
        results["pinterest"] = pinterest_results
    except Exception as e:
        logger.error("Pinterest trends sync failed: %s", e)
        results["pinterest"] = {"error": str(e)}

    try:
        amazon_service = AmazonTrendService()
        amazon_result = await amazon_service.fetch_and_process()
        results["amazon"] = amazon_result

        convex = get_convex()
        for keyword, asins in amazon_result.get("keyword_asins", {}).items():
            region = "us"
            for r in ["US", "UK", "DE", "FR", "IT", "ES"]:
                if keyword.endswith(f" {r}"):
                    region = r.lower()
                    break

            existing = await convex.products_list_by_asins(asins)
            existing_asins = {p.get("asin") for p in existing if p.get("asin")}
            matched = [a for a in asins if a in existing_asins]
            discovered = [a for a in asins if a not in existing_asins]

            await convex.pinterest_trends_save(
                keyword=keyword,
                rank=1,
                source="amazon",
                timeframe=f"amazon_daily_{region}",
                matchedAsins=matched,
                discoveredAsins=discovered,
                productCount=len(asins),
                queuedCount=0,
            )

        await amazon_service.close()
    except Exception as e:
        logger.error("Amazon trends sync failed: %s", e)
        results["amazon"] = {"error": str(e)}

    return results


async def scheduled_scrape():
    logger.info("Scheduled scrape triggered")
    scraper = get_scraper()
    scorer = ProductScorer()
    s = ScraperScheduler(scraper=scraper, scorer=scorer)
    result = await s.run()
    stored = result.get("products_stored", 0)
    logger.info("Scheduled scrape: %s products stored", stored)
    if stored > 0:
        pinterest = get_pinterest()
        queue_result = await pinterest.auto_queue_products(limit=11)
        logger.info("Auto-queued: %s products", queue_result.get("queued", 0))


async def scheduled_publish():
    logger.info("Scheduled publish triggered")
    pinterest = get_pinterest()
    queue_count = await pinterest.get_queue_count()
    if queue_count < 4:
        logger.info("Queue low (%s), auto-queuing 11 products", queue_count)
        await pinterest.auto_queue_products(limit=11)
    result = await pinterest.publish_queued_posts(limit=2)
    logger.info("Scheduled publish: %s published, %s failed",
                result.get("published", 0), result.get("failed", 0))


# ─── Lifespan manager (startup & shutdown) ─────────────────────────────
_bg_tasks: List[asyncio.Task] = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _bg_tasks
    await _load_schedule_state()
    app.state.shutdown_event = asyncio.Event()
    loop = asyncio.get_event_loop()
    loop.set_default_executor(concurrent.futures.ThreadPoolExecutor(max_workers=20))

    async def _scrape_runner():
        await _run_task_loop("scrape", app.state.shutdown_event)

    async def _publish_runner():
        await _run_task_loop("publish", app.state.shutdown_event)

    async def _trends_runner():
        await _run_task_loop("trends", app.state.shutdown_event)

    _bg_tasks = [
        asyncio.create_task(_scrape_runner(), name="scrape_loop"),
        asyncio.create_task(_publish_runner(), name="publish_loop"),
        asyncio.create_task(_trends_runner(), name="trends_loop"),
    ]
    logger.info("Background tasks started — scrape every %sh, publish every %sm, trends every %sm",
                settings.SCRAPE_INTERVAL_HOURS, settings.PUBLISH_INTERVAL_MINUTES, settings.SCRAPE_INTERVAL_HOURS * 30)
    yield
    logger.info("Server shutting down \u2014 cancelling background tasks")
    app.state.shutdown_event.set()
    for task in _bg_tasks:
        task.cancel()
    await asyncio.gather(*_bg_tasks, return_exceptions=True)
    logger.info("Background tasks stopped")


app = FastAPI(
    title="Get It Done",
    description="Amazon Affiliate Pinterest Automation System",
    version="0.1.0",
    lifespan=lifespan,
)

# ─── CORS ──────────────────────────────────────────────────────────────
_origins = [origin.strip() for origin in settings.ALLOWED_ORIGINS.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins or ["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key"],
)

# ─── Static files mount ───────────────────────────────────────────────
app.mount(f"/api/images", StaticFiles(directory=settings.PIN_IMAGE_DIR), name="images")


# ─── Background loop helpers ─────────────────────────────────────────
def _initial_delay(component: str, default: int) -> float:
    nxt = _schedule_state[component].get("next_run")
    if nxt is None:
        return float(default)
    remaining = nxt - time.time()
    if remaining <= 0:
        return 2.0
    return remaining


async def _run_task_loop(component: str, shutdown_event: asyncio.Event) -> None:
    delay = _initial_delay(component, 15 if component == "scrape" else (60 if component == "trends" else 30))
    await asyncio.sleep(delay)
    while not shutdown_event.is_set():
        try:
            if component == "scrape":
                await scheduled_scrape()
            elif component == "publish":
                await scheduled_publish()
            elif component == "trends":
                await scheduled_trends_sync()
            await _save_schedule_state(component)
            if component == "scrape":
                interval = settings.SCRAPE_INTERVAL_HOURS * 3600
            elif component == "publish":
                interval = settings.PUBLISH_INTERVAL_MINUTES * 60
            else:
                interval = settings.SCRAPE_INTERVAL_HOURS * 1800
            _schedule_state[component]["next_run"] = int(time.time() + interval)
            await asyncio.wait_for(shutdown_event.wait(), timeout=interval)
        except asyncio.TimeoutError:
            continue
        except Exception as e:
            logger.error("%s loop error: %s, retrying in 60s", component, e)
            await asyncio.sleep(60)


# ─── Pydantic models ──────────────────────────────────────────────────
class Product(BaseModel):
    convex_id: str = ""
    asin: str
    title: str
    category: Optional[str] = None
    price: Optional[float] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None
    bestseller_rank: Optional[int] = None
    trend_score: Optional[float] = None
    image_url: Optional[str] = None
    product_url: Optional[str] = None
    affiliate_url: Optional[str] = None
    source: Optional[str] = None


class PinterestPost(BaseModel):
    id: Optional[str] = None
    product_id: str
    asin: str = ""
    image_url: str
    generated_image_url: Optional[str] = None
    pin_title: str
    pin_description: str
    hashtags: Optional[List[str]] = None
    affiliate_url: str
    status: str
    scheduled_at: Optional[str] = None
    published_at: Optional[str] = None
    board_id: Optional[str] = None
    board_name: Optional[str] = None


class CreateBoardRequest(BaseModel):
    name: str
    description: str = ""


class ProductContentRequest(BaseModel):
    asin: str
    title: str
    category: Optional[str] = None
    image_url: str
    source: Optional[str] = None
    description: Optional[str] = None
    hashtags: Optional[List[str]] = None


# ─── Routes ──────────────────────────────────────────────────────────

@app.get("/health")
async def health_check():
    deps = {}
    try:
        convex = get_convex()
        await convex.settings_get("health_check")
        deps["convex"] = "ok"
    except Exception as e:
        deps["convex"] = f"error: {e}"

    pinterest = get_pinterest()
    deps["pinterest"] = "ok" if pinterest.is_configured() else "not configured"

    content_ai = get_content_ai()
    deps["nvidia_ai"] = "ok" if content_ai.is_configured() else "not configured"

    all_ok = all(v == "ok" for v in deps.values())
    return {
        "status": "healthy" if all_ok else "degraded",
        "version": "0.1.0",
        "dependencies": deps,
    }


@app.get("/api/system/status")
async def get_system_status():
    state = get_state()
    db_status = "connected" if get_convex() else "disconnected"
    return {
        "scraper": state["scraper"],
        "publisher": state["publisher"],
        "database": {"status": db_status, "last_run": None, "message": "Convex DB"},
        "scheduler": {
            "status": "running",
            "last_run": _fmt_ts(_schedule_state["scrape"]["last_run"]),
            "message": f"Scrape every {settings.SCRAPE_INTERVAL_HOURS}h, publish every {settings.PUBLISH_INTERVAL_MINUTES}m",
            "schedule": [
                {"id": "scrape_job", "next_run": _fmt_ts(_schedule_state["scrape"]["next_run"]), "interval": f"{settings.SCRAPE_INTERVAL_HOURS}h"},
                {"id": "publish_job", "next_run": _fmt_ts(_schedule_state["publish"]["next_run"]), "interval": f"{settings.PUBLISH_INTERVAL_MINUTES}m"},
                {"id": "trends_job", "next_run": _fmt_ts(_schedule_state["trends"]["next_run"]), "interval": f"{settings.SCRAPE_INTERVAL_HOURS * 30}m"},
            ],
        },
    }


@app.get("/api/stats")
async def get_stats() -> Dict[str, Any]:
    try:
        convex = get_convex()
        products = await convex.products_list(limit=1000)
        pinterest_stats = await convex.pinterest_get_stats()
        recent_logs = await convex.scraping_logs_get_recent(limit=5)
        trending_products = await convex.products_get_trending(limit=10)

        return {
            "products": {
                "total": len(products),
                "sources": _count_by_source(products),
            },
            "pinterest": pinterest_stats,
            "scraping": {
                "recent": recent_logs[:3] if recent_logs else [],
            },
            "trending": trending_products[:5] if trending_products else [],
        }
    except Exception as e:
        return {
            "products": {"total": 0, "sources": {}},
            "pinterest": {"total": 0, "queued": 0, "published": 0, "failed": 0},
            "scraping": {"recent": []},
            "trending": [],
            "error": str(e),
        }


def _count_by_source(products: List[Dict]) -> Dict[str, int]:
    counts = {}
    for p in products:
        source = p.get("source", "unknown")
        counts[source] = counts.get(source, 0) + 1
    return counts


@app.get("/api/products", response_model=List[Product])
async def get_products(
    source: Optional[str] = None,
    min_score: Optional[float] = None,
    limit: int = Query(50, ge=1, le=200),
):
    try:
        convex = get_convex()
        products_data = await convex.products_list(source=source, min_score=min_score, limit=limit)

        products = []
        for p in products_data:
            products.append(Product(
                convex_id=p.get("_id", ""),
                asin=p.get("asin", ""),
                title=p.get("title", ""),
                category=p.get("category"),
                price=p.get("currentPrice") or p.get("price"),
                rating=p.get("rating"),
                review_count=p.get("reviewCount"),
                bestseller_rank=p.get("bestsellerRank"),
                trend_score=p.get("trendScore"),
                image_url=p.get("imageUrl"),
                product_url=p.get("productUrl", ""),
                affiliate_url=p.get("affiliateUrl"),
                source=p.get("source", ""),
            ))
        return products
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/trending", response_model=List[Product])
async def get_trending_products(limit: int = Query(20, ge=1, le=100)):
    try:
        convex = get_convex()
        products_data = await convex.products_get_trending(limit=limit)

        products = []
        for p in products_data:
            products.append(Product(
                convex_id=p.get("_id", ""),
                asin=p.get("asin", ""),
                title=p.get("title", ""),
                category=p.get("category"),
                price=p.get("currentPrice") or p.get("price"),
                rating=p.get("rating"),
                review_count=p.get("reviewCount"),
                bestseller_rank=p.get("bestsellerRank"),
                trend_score=p.get("trendScore"),
                image_url=p.get("imageUrl"),
                product_url=p.get("productUrl", ""),
                affiliate_url=p.get("affiliateUrl"),
                source=p.get("source", ""),
            ))
        return products
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/affiliate/{asin}")
async def get_affiliate_link(asin: str):
    try:
        engine = get_affiliate_engine()
        link = engine.generate_affiliate_link(asin)
        return {"asin": asin, "affiliate_link": link}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/pinterest/queue")
async def get_pinterest_queue(status: Optional[str] = None):
    try:
        convex = get_convex()
        posts = await convex.pinterest_list(status=status, limit=100)
        return {"posts": posts, "count": len(posts)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/scraping/status")
async def get_scraping_status():
    try:
        convex = get_convex()
        logs = await convex.scraping_logs_get_recent(limit=5)
        return {"logs": logs, "count": len(logs)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/scheduler/scrape", dependencies=[Depends(verify_api_key)])
async def trigger_scrape(source: Optional[str] = None):
    try:
        scraper = get_scraper()
        scorer = ProductScorer()
        scraper_sched = ScraperScheduler(scraper=scraper, scorer=scorer)
        result = await scraper_sched.run(source=source)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/scheduler/publish", dependencies=[Depends(verify_api_key)])
async def trigger_publish(limit: int = Query(5, ge=1, le=20)):
    try:
        pinterest = get_pinterest()
        result = await pinterest.publish_queued_posts(limit=limit)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/pinterest/queue", dependencies=[Depends(verify_api_key)])
async def queue_post(post: PinterestPost):
    try:
        pinterest = get_pinterest()
        post_id = await pinterest.queue_post(
            product_id=post.product_id,
            asin=post.asin,
            image_url=post.image_url,
            pin_title=post.pin_title,
            pin_description=post.pin_description,
            affiliate_url=post.affiliate_url,
            generated_image_url=post.generated_image_url,
            hashtags=post.hashtags,
            board_id=post.board_id,
            board_name=post.board_name,
        )
        convex = get_convex()
        balance = await convex.pinterest_get_queue_balance()
        return {"status": "queued", "post_id": post_id, "balance": balance}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/queue/balance", dependencies=[Depends(verify_api_key)])
async def get_queue_balance():
    try:
        convex = get_convex()
        balance = await convex.pinterest_get_queue_balance()
        quotas = {
            "trending": 3,
            "bestsellers": 2,
            "new_releases": 2,
            "movers": 2,
            "deals": 2,
        }
        return {
            "current": balance,
            "quotas": quotas,
            "summary": {
                k: {"queued": balance.get(k, 0), "quota": quotas[k], "remaining": max(0, quotas[k] - balance.get(k, 0))}
                for k in quotas
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/pinterest/test", dependencies=[Depends(verify_api_key)])
async def test_pinterest():
    try:
        pinterest = get_pinterest()
        result = await pinterest.test_connection()
        return result
    except Exception as e:
        return {"success": False, "message": str(e), "boards": []}


@app.get("/api/pinterest/boards")
async def get_pinterest_boards():
    try:
        pinterest = get_pinterest()
        boards = await pinterest.get_boards()
        return {
            "boards": [{"id": b.get("id"), "name": b.get("name")} for b in boards],
            "count": len(boards),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/pinterest/boards/create", dependencies=[Depends(verify_api_key)])
async def create_pinterest_board(req: CreateBoardRequest):
    try:
        pinterest = get_pinterest()
        result = await pinterest.create_and_register_board(
            name=req.name,
            description=req.description,
        )
        if result:
            return result
        raise HTTPException(status_code=500, detail="Failed to create board")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/pinterest/status")
async def get_pinterest_status():
    pinterest = get_pinterest()
    is_configured = pinterest.is_configured()
    return {
        "configured": is_configured,
        "board_id": settings.PINTEREST_BOARD_ID if is_configured else None,
        "message": "Pinterest API configured" if is_configured else "Pinterest API not configured \u2014 set PINTEREST_ACCESS_TOKEN and PINTEREST_BOARD_ID in .env",
    }


@app.get("/api/buffer/status")
async def get_buffer_status():
    from pinterest.buffer_client import BufferClient
    client = BufferClient()
    pinterest_ok = client.has_pinterest_channel()
    twitter_ok = client.has_twitter_channel()
    channels = []
    if pinterest_ok:
        channels.append(f"Pinterest ({settings.BUFFER_PINTEREST_CHANNEL_ID[:8]}...)")
    if twitter_ok:
        channels.append(f"Twitter ({settings.BUFFER_TWITTER_CHANNEL_ID[:8]}...)")
    return {
        "configured": client.is_configured(),
        "channels": channels,
        "message": f"Buffer configured: {', '.join(channels) if channels else 'No channels'}",
    }


@app.post("/api/buffer/test", dependencies=[Depends(verify_api_key)])
async def test_buffer():
    try:
        from pinterest.buffer_client import BufferClient
        client = BufferClient()
        if not client.is_configured():
            return {"success": False, "message": "Buffer not configured"}
        result = await client.test_connection()
        return result
    except Exception as e:
        return {"success": False, "message": str(e)}


@app.get("/api/ai/status")
async def ai_status():
    content_ai = get_content_ai()
    return {
        "configured": content_ai.is_configured(),
        "provider": "NVIDIA",
        "model": settings.NVIDIA_MODEL,
    }


@app.post("/api/ai/generate-content", dependencies=[Depends(verify_api_key)])
async def generate_content(req: ProductContentRequest):
    try:
        content_ai = get_content_ai()
        result = content_ai.generate_content(req.model_dump())
        return result
    except Exception as e:
        logger.error("Content generation failed: %s", e)
        return {"title": req.title[:60], "description": "", "hashtags": []}


@app.post("/api/ai/generate-image", dependencies=[Depends(verify_api_key)])
async def generate_image(req: ProductContentRequest):
    try:
        image_gen = get_image_gen()
        description = req.description or ""
        hashtags = req.hashtags or []
        filename = await image_gen.generate_pin_image(
            product_image_url=req.image_url,
            title=req.title,
            description=description,
            hashtags=hashtags,
            asin=req.asin,
            category=req.category,
        )
        if filename:
            image_url = f"/api/images/{filename}"
            return {"image_url": image_url, "filename": filename}
        return {"image_url": req.image_url, "filename": None}
    except Exception as e:
        logger.error("Image generation failed: %s", e)
        return {"image_url": req.image_url, "filename": None}


@app.post("/api/queue/publish/{post_id}", dependencies=[Depends(verify_api_key)])
async def manual_publish_post(post_id: str):
    try:
        pinterest = get_pinterest()
        result = await pinterest.publish_one(post_id)
        if result.get("published"):
            return {"ok": True}
        return {"ok": False, "error": result.get("error", "Unknown error")}
    except Exception as e:
        logger.error("Manual publish failed: %s", e)
        return {"ok": False, "error": str(e)}


@app.get("/api/trends")
async def get_trends(source: Optional[str] = None, timeframe: Optional[str] = None):
    try:
        convex = get_convex()
        trends_data = await convex.pinterest_trends_list(source=source, timeframe=timeframe)
        return {"trends": trends_data, "count": len(trends_data)}
    except Exception as e:
        logger.error("Failed to fetch trends: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/trends/sync", dependencies=[Depends(verify_api_key)])
async def sync_trends():
    results: Dict[str, Any] = {}
    try:
        try:
            pinterest_service = PinterestTrendService()
            pinterest_results = await pinterest_service.run_all_regions(timeframe="today")
            results["pinterest"] = pinterest_results
        except Exception as e:
            logger.error("Pinterest trends sync failed: %s", e)
            results["pinterest"] = {"error": str(e)}

        try:
            amazon_service = AmazonTrendService()
            amazon_result = await amazon_service.fetch_and_process()
            results["amazon"] = amazon_result

            convex = get_convex()
            for keyword, asins in amazon_result.get("keyword_asins", {}).items():
                region = "us"
                for r in ["US", "UK", "DE", "FR", "IT", "ES"]:
                    if keyword.endswith(f" {r}"):
                        region = r.lower()
                        break

                existing = await convex.products_list_by_asins(asins)
                existing_asins = {p.get("asin") for p in existing if p.get("asin")}
                matched = [a for a in asins if a in existing_asins]
                discovered = [a for a in asins if a not in existing_asins]

                await convex.pinterest_trends_save(
                    keyword=keyword,
                    rank=1,
                    source="amazon",
                    timeframe=f"amazon_daily_{region}",
                    matchedAsins=matched,
                    discoveredAsins=discovered,
                    productCount=len(asins),
                    queuedCount=0,
                )

            await amazon_service.close()
        except Exception as e:
            logger.error("Amazon trends sync failed: %s", e)
            results["amazon"] = {"error": str(e)}

        return {"status": "completed", "results": results}
    except Exception as e:
        logger.error("Trends sync failed: %s", e)
        return {"status": "error", "error": str(e)}


@app.get("/api/trends/products")
async def get_trend_products(keyword: Optional[str] = None, timeframe: Optional[str] = None):
    try:
        convex = get_convex()
        if keyword:
            posts = await convex.pinterest_list_by_trend_keyword(keyword=keyword, timeframe=timeframe)
        else:
            posts = await convex.pinterest_list(limit=50)
        return {"posts": posts, "count": len(posts)}
    except Exception as e:
        logger.error("Failed to fetch trend products: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="::", port=8000, reload=True, timeout_keep_alive=120)
