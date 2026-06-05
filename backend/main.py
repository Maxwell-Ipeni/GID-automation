#!/usr/bin/env python
"""
Get It Done - Amazon Affiliate Pinterest Automation System
Main entry point for the FastAPI application.
"""

import asyncio
import logging
import os
import time
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from scraping.amazon_scraper import AmazonScraper
from affiliate.affiliate_engine import AffiliateEngine
from pinterest.pinterest_publisher import PinterestPublisher
from scoring.product_scorer import ProductScorer
from scheduler.scraper_scheduler import ScraperScheduler
from utils.config import get_settings
from utils.convex_client import ConvexService
from utils.state import get_state
from ai.pin_writer import PinContentAI
from images.image_generator import PinImageGenerator

settings = get_settings()

app = FastAPI(
    title="Get It Done",
    description="Amazon Affiliate Pinterest Automation System",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

scraper = AmazonScraper()
affiliate_engine = AffiliateEngine(tag=settings.AMAZON_AFFILIATE_TAG)
pinterest = PinterestPublisher(
    access_token=settings.PINTEREST_ACCESS_TOKEN,
    board_id=settings.PINTEREST_BOARD_ID
)
scorer = ProductScorer()
convex = ConvexService()
content_ai = PinContentAI()
image_gen = PinImageGenerator()

os.makedirs(settings.PIN_IMAGE_DIR, exist_ok=True)
app.mount(f"/api/images", StaticFiles(directory=settings.PIN_IMAGE_DIR), name="images")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

# In-memory schedule state for the status endpoint.
# Persisted across restarts via Convex settings keys:
#   "last_scrape_at"  — unix timestamp of last successful scrape
#   "last_publish_at" — unix timestamp of last successful publish
_schedule_state: dict = {
    "scrape": {"last_run": None, "next_run": None},
    "publish": {"last_run": None, "next_run": None},
}


async def _load_schedule_state() -> None:
    """Load last-run timestamps from Convex and compute next-run times."""
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

        logger.info(
            "Schedule state loaded — scrape next: %s, publish next: %s",
            _fmt_ts(_schedule_state["scrape"]["next_run"]),
            _fmt_ts(_schedule_state["publish"]["next_run"]),
        )
    except Exception as e:
        logger.warning("Could not load schedule state from Convex: %s", e)
        _schedule_state["scrape"]["next_run"] = int(time.time() + 15)
        _schedule_state["publish"]["next_run"] = int(time.time() + 30)


async def _save_schedule_state(component: str) -> None:
    """Persist last-run timestamp to Convex and update in-memory state."""
    try:
        ts = int(time.time())
        key = f"last_{component}_at"
        interval = (
            settings.SCRAPE_INTERVAL_HOURS * 3600
            if component == "scrape"
            else settings.PUBLISH_INTERVAL_MINUTES * 60
        )
        await convex.settings_set(key, ts)
        _schedule_state[component]["last_run"] = ts
        _schedule_state[component]["next_run"] = ts + interval
    except Exception as e:
        logger.warning("Failed to save %s schedule state: %s", component, e)


def _fmt_ts(ts: Optional[int]) -> str:
    """Format a unix timestamp as ISO for logging / API responses."""
    if ts is None:
        return ""
    from datetime import datetime
    return datetime.fromtimestamp(ts).isoformat()


async def scheduled_scrape():
    logger.info("Scheduled scrape triggered")
    s = ScraperScheduler(scraper=scraper, scorer=scorer)
    result = await s.run()
    stored = result.get('products_stored', 0)
    logger.info(f"Scheduled scrape: {stored} products stored")
    if stored > 0:
        queue_result = await pinterest.auto_queue_products(limit=5)
        logger.info(f"Auto-queued: {queue_result.get('queued', 0)} products")


async def scheduled_publish():
    logger.info("Scheduled publish triggered")
    queue_count = await pinterest.get_queue_count()
    if queue_count < 4:
        logger.info(f"Queue low ({queue_count}), auto-queuing 5 products")
        await pinterest.auto_queue_products(limit=5)
    result = await pinterest.publish_queued_posts(limit=2)
    logger.info(f"Scheduled publish: {result.get('published', 0)} published, {result.get('failed', 0)} failed")


@app.on_event("startup")
async def start_background_tasks():
    await _load_schedule_state()
    asyncio.create_task(_run_scrape_loop())
    asyncio.create_task(_run_publish_loop())
    logger.info(f"Background tasks started — scrape every {settings.SCRAPE_INTERVAL_HOURS}h, publish every {settings.PUBLISH_INTERVAL_MINUTES}m")


def _initial_delay(component: str, default: int) -> float:
    """Return seconds to wait until the next scheduled run.

    If the last run is unknown (first start) use *default* seconds.
    If the next run is past due, run immediately (small buffer).
    Otherwise sleep the remaining time.
    """
    nxt = _schedule_state[component].get("next_run")
    if nxt is None:
        return float(default)
    remaining = nxt - time.time()
    if remaining <= 0:
        return 2.0
    return remaining


async def _run_scrape_loop():
    delay = _initial_delay("scrape", 15)
    await asyncio.sleep(delay)
    while True:
        try:
            await scheduled_scrape()
            await _save_schedule_state("scrape")
            await asyncio.sleep(settings.SCRAPE_INTERVAL_HOURS * 3600)
        except Exception as e:
            logger.error(f"Scrape loop error: {e}, retrying in 60s")
            await asyncio.sleep(60)


async def _run_publish_loop():
    delay = _initial_delay("publish", 30)
    await asyncio.sleep(delay)
    while True:
        try:
            await scheduled_publish()
            await _save_schedule_state("publish")
            await asyncio.sleep(settings.PUBLISH_INTERVAL_MINUTES * 60)
        except Exception as e:
            logger.error(f"Publish loop error: {e}, retrying in 60s")
            await asyncio.sleep(60)


@app.on_event("shutdown")
async def stop_background_tasks():
    logger.info("Server shutting down — background tasks cancelled")


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


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "0.1.0"}


@app.get("/api/system/status")
async def get_system_status():
    """
    Get real-time system status for all components.
    Returns current state of scraper, publisher, database, and scheduler.
    """
    state = get_state()
    db_status = "connected" if convex else "disconnected"
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
            ],
        },
    }


@app.get("/api/stats")
async def get_stats() -> Dict[str, Any]:
    """
    Get dashboard statistics from Convex.
    """
    try:
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
            "error": str(e)
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
    limit: int = Query(50, ge=1, le=200)
):
    """
    Get products from Convex with optional filtering.
    """
    try:
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
    """
    Get the top trending products from Convex.
    """
    try:
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
    """
    Generate an affiliate link for a given ASIN.
    """
    try:
        link = affiliate_engine.generate_affiliate_link(asin)
        return {"asin": asin, "affiliate_link": link}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/pinterest/queue")
async def get_pinterest_queue(status: Optional[str] = None):
    """
    Get Pinterest posts with optional status filter.
    """
    try:
        posts = await convex.pinterest_list(status=status, limit=100)
        return {"posts": posts, "count": len(posts)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/scraping/status")
async def get_scraping_status():
    """
    Get the status of recent scraping operations.
    """
    try:
        logs = await convex.scraping_logs_get_recent(limit=5)
        return {"logs": logs, "count": len(logs)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/scheduler/scrape")
async def trigger_scrape(source: Optional[str] = None):
    """
    Manually trigger a scraping run (for testing).
    In production, scraping runs automatically via scheduler.
    """
    try:
        scraper_sched = ScraperScheduler(scraper=scraper, scorer=scorer)
        result = await scraper_sched.run(source=source)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/scheduler/publish")
async def trigger_publish(limit: int = Query(5, ge=1, le=20)):
    """
    Manually trigger publishing of queued Pinterest posts.
    In production, publishing runs automatically via scheduler.
    Phase 1: This is mocked - posts are marked as published without real Pinterest API.
    """
    try:
        result = await pinterest.publish_queued_posts(limit=limit)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/pinterest/queue")
async def queue_post(post: PinterestPost):
    """
    Queue a product for Pinterest publishing.
    """
    try:
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
        return {"status": "queued", "post_id": post_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/pinterest/test")
async def test_pinterest():
    """
    Test Pinterest API connection and credentials.
    Returns connection status and list of boards.
    """
    try:
        result = await pinterest.test_connection()
        return result
    except Exception as e:
        return {"success": False, "message": str(e), "boards": []}


@app.get("/api/pinterest/boards")
async def get_pinterest_boards():
    """
    Get list of user's Pinterest boards.
    """
    try:
        boards = await pinterest.get_boards()
        return {
            "boards": [{"id": b.get("id"), "name": b.get("name")} for b in boards],
            "count": len(boards),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class CreateBoardRequest(BaseModel):
    name: str
    description: str = ""

@app.post("/api/pinterest/boards/create")
async def create_pinterest_board(req: CreateBoardRequest):
    """Create a new Pinterest board and register it."""
    try:
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
    """
    Get Pinterest connection status and configured board info.
    """
    is_configured = pinterest.is_configured()
    return {
        "configured": is_configured,
        "board_id": settings.PINTEREST_BOARD_ID if is_configured else None,
        "message": "Pinterest API configured" if is_configured else "Pinterest API not configured - set PINTEREST_ACCESS_TOKEN and PINTEREST_BOARD_ID in .env",
    }


@app.get("/api/buffer/status")
async def get_buffer_status():
    """
    Get Buffer fallback connection status.
    """
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


@app.post("/api/buffer/test")
async def test_buffer():
    """
    Test Buffer API connection and credentials.
    """
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
    """Check if AI content generation is configured."""
    return {
        "configured": content_ai.is_configured(),
        "provider": "NVIDIA",
        "model": settings.NVIDIA_MODEL,
    }


class ProductContentRequest(BaseModel):
    asin: str
    title: str
    category: Optional[str] = None
    image_url: str
    source: Optional[str] = None
    description: Optional[str] = None
    hashtags: Optional[List[str]] = None


@app.post("/api/ai/generate-content")
async def generate_content(req: ProductContentRequest):
    """Generate AI-powered pin content (title, description, hashtags)."""
    try:
        result = content_ai.generate_content(req.model_dump())
        return result
    except Exception as e:
        logger.error(f"Content generation failed: {e}")
        return {"title": req.title[:60], "description": "", "hashtags": []}


@app.post("/api/ai/generate-image")
async def generate_image(req: ProductContentRequest):
    """Generate a custom pin image for a product."""
    try:
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
        logger.error(f"Image generation failed: {e}")
        return {"image_url": req.image_url, "filename": None}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)