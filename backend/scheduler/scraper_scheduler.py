"""
Scheduler for scraping Amazon products.
Handles automated scraping jobs and Convex logging.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional, List
from scraping.amazon_scraper import AmazonScraper
from scoring.product_scorer import ProductScorer
from utils.convex_client import ConvexService

logger = logging.getLogger(__name__)


class ScraperScheduler:
    def __init__(self, scraper: AmazonScraper, scorer: Optional[ProductScorer] = None):
        self.scraper = scraper
        self.scorer = scorer or ProductScorer()
        self.is_running = False
        self._convex: Optional[ConvexService] = None
    
    @property
    def convex(self) -> ConvexService:
        """Lazy-load Convex service."""
        if self._convex is None:
            self._convex = ConvexService()
        return self._convex
    
    async def run(self, source: Optional[str] = None) -> Dict:
        """
        Run the scraping scheduler.
        If source is specified, scrape only that source.
        Otherwise, scrape all sources.
        """
        self.is_running = True
        log_id = None
        start_time = int(datetime.now().timestamp() * 1000)
        
        try:
            source_name = source or "all"
            
            log_id = await self.convex.scraping_logs_start(source=source_name, startedAt=start_time)
            
            if source:
                results = await self._scrape_single_source(source)
            else:
                results = await self._scrape_all_sources()
            
            stored_count = await self.scraper.store_products_to_convex(results)
            
            ranked_products = self.scorer.rank_products(results)
            
            for product in ranked_products:
                try:
                    await self._update_product_score_in_convex(product)
                except Exception as e:
                    logger.error(f"Failed to update score for {product.asin}: {e}")
            
            completed_time = int(datetime.now().timestamp() * 1000)
            await self.convex.scraping_logs_complete(log_id=log_id, products_found=stored_count, completedAt=completed_time)
            
            return {
                "status": "completed",
                "timestamp": datetime.now().isoformat(),
                "source": source_name,
                "products_found": len(results),
                "products_stored": stored_count,
                "log_id": log_id
            }
        except Exception as e:
            logger.error(f"Scraping failed: {e}")
            if log_id:
                try:
                    error_time = int(datetime.now().timestamp() * 1000)
                    await self.convex.scraping_logs_failed(log_id=log_id, errors=[str(e)])
                except Exception as log_error:
                    logger.error(f"Failed to log error to Convex: {log_error}")
            return {
                "status": "error",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
        finally:
            self.is_running = False
    
    async def _scrape_single_source(self, source: str) -> List:
        """Scrape a single source."""
        if source == "bestsellers":
            products = await self.scraper.scrape_bestsellers()
            for p in products:
                p.source = "bestsellers"
        elif source == "movers":
            products = await self.scraper.scrape_movers()
            for p in products:
                p.source = "movers"
        elif source == "new_releases":
            products = await self.scraper.scrape_new_releases()
            for p in products:
                p.source = "new_releases"
        elif source == "deals":
            products = await self.scraper.scrape_deals()
            for p in products:
                p.source = "deals"
        else:
            products = []
        return products
    
    async def _scrape_all_sources(self) -> List:
        """Scrape all Amazon sources."""
        return await self.scraper.scrape_all()
    
    async def _update_product_score_in_convex(self, product) -> None:
        """Update a product's trend score in Convex."""
        try:
            from utils.config import get_settings
            from affiliate.affiliate_engine import AffiliateEngine
            settings = get_settings()
            product_url = f"{settings.AMAZON_BASE_URL}/dp/{product.asin}"
            affiliate_url = AffiliateEngine().generate_affiliate_link(product.asin)
            
            data = {
                "asin": product.asin,
                "title": product.title,
                "productUrl": product_url,
                "affiliateUrl": affiliate_url,
                "source": product.source or "unknown",
            }
            if product.category is not None:
                data["category"] = product.category
            if product.price is not None:
                data["price"] = product.price
            if product.rating is not None:
                data["rating"] = product.rating
            if product.review_count is not None:
                data["reviewCount"] = product.review_count
            if product.bestseller_rank is not None:
                data["bestsellerRank"] = product.bestseller_rank
            if product.trend_score is not None:
                data["trendScore"] = product.trend_score
            if product.image_url is not None:
                data["imageUrl"] = product.image_url
            await self.convex.products_upsert(data)
        except Exception as e:
            logger.error(f"Failed to update product score in Convex: {e}")