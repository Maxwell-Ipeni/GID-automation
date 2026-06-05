"""
Scheduler for publishing to Pinterest.
Handles scheduled publishing with retry logic.
"""

import asyncio
import logging
import random
import time
from datetime import datetime
from typing import Dict, Optional
from pinterest.pinterest_publisher import PinterestPublisher
from utils.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class PublishScheduler:
    def __init__(self, pinterest: PinterestPublisher):
        self.pinterest = pinterest
        self.is_running = False
    
    async def run(self, limit: int = 5) -> Dict:
        """
        Run the publishing scheduler.
        
        Process up to `limit` queued posts:
        1. Calculate scheduled time (15-45 min in future)
        2. Attempt to publish with Pinterest API
        3. If failed, retry once after 5 seconds
        4. If still failed, mark as failed (manual retry needed)
        
        Args:
            limit: Maximum number of posts to process
            
        Returns:
            Dict with status: published count, failed count, details
        """
        self.is_running = True
        
        try:
            if not self.pinterest.is_configured():
                logger.warning("Pinterest not configured - using mock mode")
                return await self._run_mock(limit)
            
            return await self._run_real(limit)
            
        except Exception as e:
            logger.error(f"Publish scheduler error: {e}")
            return {
                "status": "error",
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "published": 0,
                "failed": 0,
            }
        finally:
            self.is_running = False
    
    async def _run_real(self, limit: int) -> Dict:
        """Run real Pinterest publishing."""
        result = await self.pinterest.publish_queued_posts(limit=limit)
        result["timestamp"] = datetime.now().isoformat()
        result["status"] = "completed"
        return result
    
    async def _run_mock(self, limit: int) -> Dict:
        """Run mock publishing (Phase 1 behavior - for testing without credentials)."""
        try:
            return await self.pinterest.publish_queued_posts_mock(limit=limit)
        except Exception as e:
            logger.error(f"Mock publish error: {e}")
            return {
                "status": "error",
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "published": 0,
                "failed": 0,
            }
    
    def calculate_schedule_time(self) -> int:
        """
        Calculate a random schedule time 15-45 minutes in the future.
        
        Returns:
            Unix timestamp for scheduled publish
        """
        delay_min = settings.PUBLISH_DELAY_MIN_MINUTES
        delay_max = settings.PUBLISH_DELAY_MAX_MINUTES
        delay_seconds = random.randint(delay_min * 60, delay_max * 60)
        return int(time.time()) + delay_seconds
    
    async def schedule_post(
        self,
        post_id: str,
        post_data: Dict,
        scheduled_at: Optional[int] = None
    ) -> Dict:
        """
        Schedule a single post for future publishing.
        
        Args:
            post_id: Convex post ID
            post_data: Post data dict
            scheduled_at: Unix timestamp (calculated if not provided)
            
        Returns:
            Dict with scheduling result
        """
        if scheduled_at is None:
            scheduled_at = self.calculate_schedule_time()
        
        try:
            # Update Convex with scheduled time
            self.pinterest.schedule_post(post_id, scheduled_at)
            
            return {
                "status": "scheduled",
                "post_id": post_id,
                "scheduled_at": scheduled_at,
                "scheduled_at_formatted": datetime.fromtimestamp(scheduled_at).isoformat(),
            }
        except Exception as e:
            logger.error(f"Failed to schedule post {post_id}: {e}")
            return {
                "status": "error",
                "post_id": post_id,
                "error": str(e),
            }