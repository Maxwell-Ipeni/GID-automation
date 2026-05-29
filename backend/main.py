#!/usr/bin/env python
"""
Get It Done - Amazon Affiliate Pinterest Automation System
Main entry point for the FastAPI application.
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

from scraping.amazon_scraper import AmazonScraper
from affiliate.affiliate_engine import AffiliateEngine
from pinterest.pinterest_publisher import PinterestPublisher
from scoring.product_scorer import ProductScorer
from scheduler.scraper_scheduler import ScraperScheduler
from scheduler.publish_scheduler import PublishScheduler
from utils.config import get_settings

# Load settings
settings = get_settings()

# Initialize FastAPI app
app = FastAPI(
    title="Get It Done",
    description="Amazon Affiliate Pinterest Automation System",
    version="0.1.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
scraper = AmazonScraper()
affiliate_engine = AffiliateEngine(tag=settings.AMAZON_AFFILIATE_TAG)
pinterest = PinterestPublisher(
    access_token=settings.PINTEREST_ACCESS_TOKEN,
    board_id=settings.PINTEREST_BOARD_ID
)
scorer = ProductScorer()

# Request/Response Models
class Product(BaseModel):
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
    source: Optional[str] = None

class PinterestPost(BaseModel):
    id: Optional[str] = None
    product_id: str
    image_url: str
    pin_title: str
    pin_description: str
    affiliate_url: str
    status: str
    scheduled_at: Optional[str] = None
    published_at: Optional[str] = None

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "0.1.0"}

@app.get("/api/products", response_model=List[Product])
async def get_products(
    source: Optional[str] = None,
    min_score: Optional[float] = None,
    limit: int = Query(50, ge=1, le=200)
):
    """
    Get products from the database with optional filtering.
    """
    try:
        products = await scraper.get_stored_products(source=source, min_score=min_score, limit=limit)
        return products
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/products/refresh")
async def refresh_products():
    """
    Manually trigger a product scraping run.
    """
    try:
        results = await scraper.scrape_all()
        return {"status": "success", "products_found": len(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/trending", response_model=List[Product])
async def get_trending_products(limit: int = Query(20, ge=1, le=100)):
    """
    Get the top trending products based on the scoring engine.
    """
    try:
        products = await scraper.get_stored_products()
        ranked = scorer.rank_products(products)
        return ranked[:limit]
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

@app.post("/api/pinterest/queue")
async def queue_pinterest_post(post: PinterestPost):
    """
    Queue a product for Pinterest publishing.
    """
    try:
        # Store in publishing queue (simplified)
        return {"status": "queued", "product_id": post.product_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/pinterest/queue")
async def get_pinterest_queue():
    """
    Get the current Pinterest publishing queue.
    """
    try:
        # Retrieve queue from database (simplified)
        return {"queue": []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/pinterest/publish")
async def publish_to_pinterest(post_id: str):
    """
    Publish a queued item to Pinterest.
    """
    try:
        result = await pinterest.publish_pin(post_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/scraping/status")
async def get_scraping_status():
    """
    Get the status of the most recent scraping operation.
    """
    try:
        status = await scraper.get_scraping_status()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/scheduler/scrape")
async def schedule_scraping():
    """
    Start the scraping scheduler job.
    """
    try:
        scheduler = ScraperScheduler(scraper=scraper)
        await scheduler.run()
        return {"status": "scraping_scheduled"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/scheduler/publish")
async def schedule_publishing():
    """
    Start the publishing scheduler job.
    """
    try:
        scheduler = PublishScheduler(pinterest=pinterest)
        await scheduler.run()
        return {"status": "publishing_scheduled"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
