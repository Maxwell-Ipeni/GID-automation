"""
Convex client helper for backend operations.
Provides simple wrappers for Convex mutations and queries.
"""

import asyncio
import time
from convex import ConvexClient
from utils.config import get_settings
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)

_client: Optional[ConvexClient] = None


def get_convex_client() -> ConvexClient:
    """Get or create the Convex client singleton."""
    global _client
    if _client is None:
        settings = get_settings()
        if not settings.CONVEX_URL:
            raise ValueError("CONVEX_URL not set in configuration")
        _client = ConvexClient(settings.CONVEX_URL)
    return _client


def reset_client():
    """Reset the client (useful for testing or reconfiguration)."""
    global _client
    _client = None


class ConvexService:
    """Service class for Convex database operations."""

    def __init__(self):
        self.client = get_convex_client()

    async def products_upsert(self, product_data: Dict[str, Any]) -> str:
        """Insert or update a product in Convex."""
        try:
            result = await asyncio.to_thread(self.client.mutation, "products:upsert", product_data)
            return result
        except Exception as e:
            logger.error(f"Failed to upsert product: {e}")
            raise

    async def products_list(self, source: Optional[str] = None, min_score: Optional[float] = None, limit: int = 50) -> List[Dict]:
        """List products from Convex."""
        args = {"limit": limit}
        if source:
            args["source"] = source
        if min_score is not None:
            args["minScore"] = min_score
        return await asyncio.to_thread(self.client.query, "products:list", args)

    async def products_get_trending(self, limit: int = 20) -> List[Dict]:
        """Get trending products."""
        return await asyncio.to_thread(self.client.query, "products:getTrending", {"limit": limit})

    async def products_get_source_counts(self) -> Dict:
        """Get product count and source breakdown."""
        return await asyncio.to_thread(self.client.query, "products:getSourceCounts", {})

    async def products_list_by_title(self, title: str) -> List[Dict]:
        """Find products by exact title match."""
        return await asyncio.to_thread(self.client.query, "products:listByTitle", {"title": title})

    async def pinterest_delete(self, post_id: str) -> None:
        """Delete a Pinterest post by ID."""
        await asyncio.to_thread(self.client.mutation, "pinterest:remove", {"id": post_id})

    async def affiliate_generate(self, product_id: str, asin: str, affiliate_tag: str) -> Dict:
        """Generate an affiliate link for a product."""
        return await asyncio.to_thread(self.client.mutation, "affiliate:generateAffiliateLink", {
            "productId": product_id,
            "asin": asin,
            "affiliateTag": affiliate_tag
        })

    async def affiliate_get_by_product(self, product_id: str) -> Optional[Dict]:
        """Get affiliate link for a product."""
        return await asyncio.to_thread(self.client.query, "affiliate:getByProduct", {"productId": product_id})

    async def pinterest_list_all_product_ids(self) -> set:
        """Get all product IDs with queued or processing status (ineligible for re-queue)."""
        ids = await asyncio.to_thread(self.client.query, "pinterest:listQueuedProductIds", {})
        return set(ids)

    async def pinterest_list(self, status: Optional[str] = None, board_id: Optional[str] = None, limit: int = 50) -> List[Dict]:
        """List Pinterest posts."""
        args = {"limit": limit}
        if status:
            args["status"] = status
        if board_id:
            args["boardId"] = board_id
        return await asyncio.to_thread(self.client.query, "pinterest:list", args)

    async def pinterest_queue(self, post_data: Dict[str, Any]) -> str:
        """Queue a Pinterest post."""
        return await asyncio.to_thread(self.client.mutation, "pinterest:queue", post_data)

    async def pinterest_update_board(self, post_id: str, board_id: str, board_name: str) -> None:
        """Update the board assignment for a Pinterest post."""
        await asyncio.to_thread(self.client.mutation, "pinterest:updateBoard", {
            "postId": post_id,
            "boardId": board_id,
            "boardName": board_name,
        })

    async def pinterest_list_boards(self) -> List[Dict]:
        """List all known Pinterest boards from Convex."""
        return await asyncio.to_thread(self.client.query, "pinterest:listBoards", {})

    async def pinterest_create_board(self, name: str, description: Optional[str] = None) -> str:
        """Register a board in Convex."""
        return await asyncio.to_thread(self.client.mutation, "pinterest:createBoard", {
            "name": name,
            "description": description or "",
        })

    async def pinterest_publish(self, post_id: str, pin_id: str, published_at: int) -> None:
        """Mark a Pinterest post as published."""
        await asyncio.to_thread(self.client.mutation, "pinterest:publish", {
            "postId": post_id,
            "pinId": pin_id,
            "publishedAt": published_at,
        })

    async def pinterest_mark_processing(self, post_id: str) -> None:
        """Mark a Pinterest post as processing (lock to prevent duplicate publishing)."""
        await asyncio.to_thread(self.client.mutation, "pinterest:markProcessing", {
            "postId": post_id,
        })

    async def pinterest_mark_failed(self, post_id: str, error_message: str) -> None:
        """Mark a Pinterest post as failed."""
        await asyncio.to_thread(self.client.mutation, "pinterest:markFailed", {
            "postId": post_id,
            "errorMessage": error_message
        })

    async def pinterest_get_stats(self) -> Dict:
        """Get Pinterest posting statistics."""
        return await asyncio.to_thread(self.client.query, "pinterest:getStats", {})

    async def pinterest_get_queue_count(self) -> int:
        """Count posts with 'queued' status."""
        return await asyncio.to_thread(self.client.query, "pinterest:getQueueCount", {})

    async def products_list_by_asins(self, asins: List[str]) -> List[Dict]:
        """Batch lookup products by ASIN list."""
        return await asyncio.to_thread(
            self.client.query, "products:listByAsins", {"asins": asins}
        )

    async def products_get_by_sources(self, sources: List[str], limit: int = 2) -> List[Dict]:
        """Get top products by source, ordered by trendScore."""
        return await asyncio.to_thread(
            self.client.query, "products:getBySources", {"sources": sources, "limit": limit}
        )

    async def pinterest_list_trending_product_ids(self) -> List[str]:
        """Get product IDs that have been queued via trends (have trendKeyword set)."""
        return await asyncio.to_thread(
            self.client.query, "pinterest:listTrendingProductIds", {}
        )

    async def pinterest_get_queue_balance(self) -> Dict[str, int]:
        """Get current queue counts by source category."""
        return await asyncio.to_thread(
            self.client.query, "pinterest:getQueueBalance", {}
        )

    async def pinterest_list_by_priority(
        self, status: Optional[str] = None, limit: int = 50
    ) -> List[Dict]:
        """List Pinterest posts ordered by priority desc, then creation time asc."""
        args = {"limit": limit}
        if status:
            args["status"] = status
        return await asyncio.to_thread(
            self.client.query, "pinterest:listByPriority", args
        )

    async def pinterest_trends_save(
        self,
        keyword: str,
        rank: int,
        source: str,
        timeframe: str,
        matchedAsins: List[str],
        discoveredAsins: List[str],
        productCount: int,
        queuedCount: int,
    ) -> str:
        """Save or update a trend entry in Convex."""
        return await asyncio.to_thread(self.client.mutation, "pinterest:trendsSave", {
            "keyword": keyword,
            "rank": rank,
            "source": source,
            "timeframe": timeframe,
            "matchedAsins": matchedAsins,
            "discoveredAsins": discoveredAsins,
            "productCount": productCount,
            "queuedCount": queuedCount,
        })

    async def pinterest_trends_list(
        self,
        source: Optional[str] = None,
        timeframe: Optional[str] = None,
    ) -> List[Dict]:
        """List stored trends, optionally filtered by source and/or timeframe."""
        args: Dict[str, Any] = {}
        if source:
            args["source"] = source
        if timeframe:
            args["timeframe"] = timeframe
        return await asyncio.to_thread(
            self.client.query, "pinterest:trendsList", args
        )

    async def pinterest_list_by_trend_keyword(
        self,
        keyword: str,
        timeframe: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict]:
        """List Pinterest posts filtered by trend keyword."""
        args = {"keyword": keyword, "limit": limit}
        if timeframe:
            args["timeframe"] = timeframe
        return await asyncio.to_thread(
            self.client.query, "pinterest:listByTrendKeyword", args
        )

    async def scraping_logs_start(self, source: str, startedAt: int = None) -> str:
        """Log the start of a scraping operation."""
        if startedAt is None:
            startedAt = int(time.time() * 1000)
        return await asyncio.to_thread(self.client.mutation, "scrapingLogs:logStart", {
            "source": source,
            "startedAt": startedAt,
        })

    async def scraping_logs_complete(self, log_id: str, products_found: int, completedAt: int = None) -> None:
        """Log the completion of a scraping operation."""
        if completedAt is None:
            completedAt = int(time.time() * 1000)
        await asyncio.to_thread(self.client.mutation, "scrapingLogs:logComplete", {
            "logId": log_id,
            "productsFound": products_found,
            "completedAt": completedAt,
        })

    async def scraping_logs_failed(self, log_id: str, errors: List[str], completedAt: int = None) -> None:
        """Log a failed scraping operation."""
        await asyncio.to_thread(self.client.mutation, "scrapingLogs:logFailed", {
            "logId": log_id,
            "errors": errors
        })

    async def scraping_logs_get_recent(self, limit: int = 10) -> List[Dict]:
        """Get recent scraping logs."""
        return await asyncio.to_thread(self.client.query, "scrapingLogs:getRecent", {"limit": limit})

    async def settings_get(self, key: str) -> Optional[Any]:
        """Get a setting value."""
        return await asyncio.to_thread(self.client.query, "settings:get", {"key": key})

    async def settings_set(self, key: str, value: Any) -> None:
        """Set a setting value."""
        await asyncio.to_thread(self.client.mutation, "settings:set", {"key": key, "value": value})