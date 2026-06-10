"""
Pinterest Publisher
Handles publishing to Pinterest via API and Convex queue management.
Phase 2: Real Pinterest API integration with scheduling and retry.
"""

import asyncio
import logging
import random
import time
from typing import Any, Dict, List, Optional
from utils.config import get_settings
from utils.convex_client import ConvexService
from utils.state import update_state

logger = logging.getLogger(__name__)
settings = get_settings()


class PinterestPublisher:
    def __init__(self, access_token: str = None, board_id: str = None):
        self.access_token = access_token or settings.PINTEREST_ACCESS_TOKEN
        self.board_id = board_id or settings.PINTEREST_BOARD_ID
        self.base_url = settings.PINTEREST_API_BASE
        self._convex: Optional[ConvexService] = None
        self._api_client = None
    
    @property
    def convex(self) -> ConvexService:
        """Lazy-load Convex service."""
        if self._convex is None:
            self._convex = ConvexService()
        return self._convex
    
    def get_api_client(self):
        """Get or create Pinterest API client."""
        if self._api_client is None:
            from pinterest.api_client import PinterestApiClient
            self._api_client = PinterestApiClient(
                access_token=self.access_token,
            )
        return self._api_client
    
    async def queue_post(
        self,
        product_id: str,
        asin: str,
        image_url: str,
        pin_title: str,
        pin_description: str,
        affiliate_url: str,
        generated_image_url: Optional[str] = None,
        hashtags: Optional[List[str]] = None,
        scheduled_at: Optional[int] = None,
        board_id: Optional[str] = None,
        board_name: Optional[str] = None,
        priority: Optional[int] = None,
        trend_keyword: Optional[str] = None,
        trend_timeframe: Optional[str] = None,
    ) -> str:
        """
        Queue a Pinterest post in Convex.
        Returns the Convex post ID.
        """
        try:
            post_data = {
                "productId": product_id,
                "asin": asin,
                "imageUrl": image_url,
                "pinTitle": pin_title,
                "pinDescription": pin_description,
                "affiliateUrl": affiliate_url,
            }
            if generated_image_url:
                post_data["generatedImageUrl"] = generated_image_url
            if hashtags:
                post_data["hashtags"] = hashtags
            if scheduled_at:
                post_data["scheduledAt"] = scheduled_at
            if board_id:
                post_data["boardId"] = board_id
            if board_name:
                post_data["boardName"] = board_name
            if priority is not None:
                post_data["priority"] = priority
            if trend_keyword:
                post_data["trendKeyword"] = trend_keyword
            if trend_timeframe:
                post_data["trendTimeframe"] = trend_timeframe
            
            post_id = await self.convex.pinterest_queue(post_data)
            logger.info(f"Queued Pinterest post: {post_id}")
            return post_id
        except Exception as e:
            logger.error(f"Failed to queue post: {e}")
            raise

    async def get_queue_count(self) -> int:
        return await self.convex.pinterest_get_queue_count()

    async def ensure_board_exists(self, board_name: str) -> Optional[str]:
        """Ensure a Pinterest board exists, creating it if needed. Returns board ID."""
        try:
            api = self.get_api_client()
            existing = await api.get_board_id_by_name(board_name)
            if existing:
                logger.debug(f"Board '{board_name}' already exists: {existing}")
                return existing
            board = await api.create_board(
                name=board_name,
                description=f"Curated {board_name.lower()} — affiliate finds",
            )
            board_id = board.get("id")
            logger.info(f"Created new Pinterest board: '{board_name}' ({board_id})")
            return board_id
        except Exception as e:
            logger.warning(f"Could not ensure board '{board_name}': {e}")
            return None

    async def _resolve_board_for_post(self, post: Dict) -> Optional[str]:
        """Resolve and persist board assignment for a post. Returns board ID or None."""
        post_id = post.get("_id")
        board_id = post.get("boardId")
        if board_id:
            return board_id

        category = None
        product_id = post.get("productId")
        if product_id:
            try:
                products = await self.convex.products_list(limit=1)
                for p in products:
                    if p.get("_id") == product_id:
                        category = p.get("category")
                        break
            except Exception:
                pass

        from images.pin_templates import get_board_name_for_category
        board_name = post.get("boardName") or get_board_name_for_category(category)

        if self.is_configured():
            resolved_id = await self.ensure_board_exists(board_name)
        else:
            resolved_id = None

        if post_id and resolved_id:
            try:
                await self.convex.pinterest_update_board(post_id, resolved_id, board_name)
            except Exception as e:
                logger.warning(f"Failed to persist board for {post_id}: {e}")

        return resolved_id
    
    async def publish_queued_posts(self, limit: int = 5) -> Dict:
        """
        Process and publish queued posts using real Pinterest API.
        
        Flow per post:
        1. Get next queued post from Convex
        2. Calculate schedule time (15-45 min in future)
        3. Create pin via Pinterest API with schedule
        4. On success: mark as published in Convex
        5. On failure: retry once after 5 seconds
        6. If still failing: try Buffer.com API as fallback
        7. On Buffer success: mark as published
        8. If Buffer also fails: mark as failed
        """
        update_state("publisher", "publishing", f"Processing up to {limit} queued posts")
        try:
            queued_posts = await self.convex.pinterest_list_by_priority(status="queued", limit=limit * 3)
            
            if not queued_posts:
                update_state("publisher", "idle", "No queued posts")
                return {"published": 0, "failed": 0, "message": "No queued posts"}

            # Check if Pinterest is configured
            if not self.is_configured():
                if self.is_buffer_configured():
                    logger.info("Pinterest not configured - publishing via Buffer")
                    return await self._publish_queued_via_buffer(limit=limit)
                logger.warning("Pinterest not configured - falling back to mock")
                return await self.publish_queued_posts_mock(limit=limit)

            api = self.get_api_client()
            
            published_count = 0
            failed_count = 0
            errors = []
            posts_to_process = queued_posts[:]
            processed_ids: set = set()

            while posts_to_process and (published_count + failed_count) < limit:
                post = posts_to_process.pop(0)
                post_id = post.get("_id")
                if not post_id or post_id in processed_ids:
                    continue
                processed_ids.add(post_id)
                
                try:
                    await self.convex.pinterest_mark_processing(post_id)
                    board_id = await self._resolve_board_for_post(post)
                    if not board_id:
                        raise ValueError("Could not resolve board for post")

                    scheduled_at = self._calculate_schedule_time()
                    pin_data = await self._real_publish_with_retry(post, scheduled_at, board_id)
                    await self._safe_mark_published(post_id, pin_data.get("id", "unknown"))
                    published_count += 1
                    logger.info(f"Successfully published post {post_id} as pin {pin_data.get('id')} on board {board_id}")
                    
                except Exception as e:
                    pinterest_error = str(e)
                    logger.error(f"Failed to publish post {post_id} after retries: {pinterest_error}")

                    buffer_result = await self._publish_via_buffer(post)
                    if buffer_result:
                        await self._safe_mark_published(post_id, f"buffer_{buffer_result}")
                        published_count += 1
                        logger.info(f"Published post {post_id} via Buffer fallback: {buffer_result}")
                        continue

                    await self.mark_failed(post_id, f"Pinterest failed, Buffer also failed. Pinterest error: {pinterest_error}")
                    errors.append({"post_id": post_id, "error": pinterest_error})
                    failed_count += 1

                    # Fill-on-failure: grab another queued post to maintain publish target
                    target_remaining = limit - (published_count + failed_count)
                    if target_remaining > 0:
                        extra_posts = await self.convex.pinterest_list(status="queued", limit=target_remaining)
                        for extra in extra_posts:
                            extra_id = extra.get("_id")
                            if extra_id and extra_id not in processed_ids and extra not in posts_to_process:
                                posts_to_process.append(extra)
            
            update_state("publisher", "completed", f"Published {published_count}, failed {failed_count}")
            return {
                "published": published_count,
                "failed": failed_count,
                "message": f"Processed {published_count + failed_count} posts",
                "errors": errors if errors else None,
            }
        except Exception as e:
            logger.error(f"Error in publish_queued_posts: {e}")
            update_state("publisher", "error", str(e))
            return {"published": 0, "failed": 0, "error": str(e)}

    async def publish_one(self, post_id: str) -> Dict:
        """Publish a single queued post by ID. Returns dict with 'published' or 'failed' key."""
        try:
            post = await self.convex.pinterest_list(status="queued", limit=100)
            post = next((p for p in post if p.get("_id") == post_id), None)
            if not post:
                return {"failed": True, "error": f"Post {post_id} not found in queue"}

            if not self.is_configured():
                if self.is_buffer_configured():
                    await self.convex.pinterest_mark_processing(post_id)
                    results = await self._post_to_buffer_channels(post)
                    any_success = "pinterest" in results or "twitter" in results
                    if not any_success:
                        raise Exception("Buffer publish failed")
                    await self._safe_mark_published(post_id, f"buffer_{results.get('pinterest', results.get('twitter', 'unknown'))}")
                    return {"published": True, "post_id": post_id}
                return {"failed": True, "error": "Pinterest not configured"}

            api = self.get_api_client()
            await self.convex.pinterest_mark_processing(post_id)
            board_id = await self._resolve_board_for_post(post)
            if not board_id:
                raise ValueError("Could not resolve board")
            scheduled_at = self._calculate_schedule_time()
            pin_data = await self._real_publish_with_retry(post, scheduled_at, board_id)
            await self._safe_mark_published(post_id, pin_data.get("id", "unknown"))
            return {"published": True, "post_id": post_id, "pin_id": pin_data.get("id")}
        except Exception as e:
            logger.error(f"Manual publish failed for {post_id}: {e}")
            buffer_result = await self._publish_via_buffer(post) if 'post' in dir() else None
            if buffer_result:
                await self._safe_mark_published(post_id, f"buffer_{buffer_result}")
                return {"published": True, "post_id": post_id}
            await self.mark_failed(post_id, str(e))
            return {"failed": True, "error": str(e)}
    
    async def _real_publish_with_retry(
        self,
        post: Dict,
        scheduled_at: int,
        board_id: str,
    ) -> Dict:
        """
        Attempt to publish a post to Pinterest with one retry on failure.
        
        Args:
            post: Post data from Convex
            scheduled_at: Unix timestamp for scheduling
            board_id: Pinterest board ID to publish to
            
        Returns:
            Pin data from Pinterest API
            
        Raises:
            PinterestApiError if both attempts fail
        """
        api = self.get_api_client()
        error = None
        
        for attempt in range(settings.PUBLISH_RETRY_ATTEMPTS + 1):
            try:
                # Create pin via Pinterest API
                pin_data = await api.create_pin(
                    board_id=board_id,
                    title=post.get("pinTitle", "Product"),
                    description=post.get("pinDescription", ""),
                    link=post.get("affiliateUrl", ""),
                    image_url=self._get_image_url(post),
                    scheduled_at=scheduled_at,
                )
                return pin_data
                
            except Exception as e:
                error = e
                logger.warning(f"Pinterest API attempt {attempt + 1} failed: {e}")
                
                if attempt < settings.PUBLISH_RETRY_ATTEMPTS:
                    # Wait before retry
                    await asyncio.sleep(settings.PUBLISH_RETRY_DELAY_SECONDS)
        
        # All attempts failed
        raise error or Exception("Unknown error during Pinterest publish")
    
    def _calculate_schedule_time(self) -> int:
        """Calculate random schedule time 15-45 minutes in future."""
        delay_min = settings.PUBLISH_DELAY_MIN_MINUTES * 60
        delay_max = settings.PUBLISH_DELAY_MAX_MINUTES * 60
        delay = random.randint(delay_min, delay_max)
        return int(time.time()) + delay
    
    async def publish_queued_posts_mock(self, limit: int = 5) -> Dict:
        """
        Mock publishing for testing without Pinterest credentials.
        Marks posts as published without calling the API.
        """
        update_state("publisher", "publishing", f"Mock publishing up to {limit} posts")
        try:
            queued_posts = await self.convex.pinterest_list(status="queued", limit=limit)
            
            if not queued_posts:
                return {"published": 0, "failed": 0, "message": "No queued posts"}
            
            published_count = 0
            failed_count = 0
            
            for post in queued_posts:
                post_id = post.get("_id")
                if not post_id:
                    continue
                
                try:
                    # Generate mock pin ID
                    pin_id = "mock_" + "".join(random.choices("abcdefghijklmnopqrstuvwxyz0123456789", k=12))
                    published_at = int(time.time() * 1000)
                    
                    await self.convex.pinterest_publish(
                        post_id=post_id,
                        pin_id=pin_id,
                        published_at=published_at
                    )
                    published_count += 1
                    logger.info(f"Mock published post: {post_id}")
                    
                except Exception as e:
                    logger.error(f"Mock publish failed for {post_id}: {e}")
                    await self.mark_failed(post_id, str(e))
                    failed_count += 1
            
            update_state("publisher", "completed", f"Mock published {published_count} posts")
            return {
                "published": published_count,
                "failed": failed_count,
                "message": f"Mock published {published_count} posts (mode: mock)",
            }
        except Exception as e:
            logger.error(f"Error in mock publish: {e}")
            update_state("publisher", "error", str(e))
            return {"published": 0, "failed": 0, "error": str(e)}
    
    async def mark_failed(self, post_id: str, error_message: str) -> None:
        """Mark a Pinterest post as failed in Convex."""
        try:
            await self.convex.pinterest_mark_failed(post_id=post_id, error_message=error_message)
            logger.info(f"Marked post as failed: {post_id}")
        except Exception as e:
            logger.error(f"Failed to mark post as failed: {e}")

    async def _post_to_buffer_channels(self, post: Dict) -> Dict[str, str]:
        """Post to all configured Buffer channels. Returns {channel_key: post_id} dict."""
        from pinterest.buffer_client import BufferClient
        client = BufferClient()
        text = post.get("pinDescription", "")
        image_url = self._get_image_url(post)
        link = post.get("affiliateUrl", "")
        results = {}

        if client.has_pinterest_channel():
            try:
                pid = await client.create_pin(
                    channel_id=settings.BUFFER_PINTEREST_CHANNEL_ID,
                    text=text,
                    image_url=image_url,
                    link=link,
                )
                results["pinterest"] = pid
                logger.info(f"Buffer Pinterest post: {pid}")
            except Exception as e:
                logger.warning(f"Buffer Pinterest channel failed: {e}")
                results["pinterest_error"] = str(e)

        if client.has_twitter_channel():
            try:
                tid = await client.create_pin(
                    channel_id=settings.BUFFER_TWITTER_CHANNEL_ID,
                    text=text,
                    image_url=image_url,
                    link=link,
                    is_twitter=True,
                )
                results["twitter"] = tid
                logger.info(f"Buffer Twitter post: {tid}")
            except Exception as e:
                logger.warning(f"Buffer Twitter channel failed: {e}")
                results["twitter_error"] = str(e)

        return results

    async def _publish_queued_via_buffer(self, limit: int = 5) -> Dict:
        """Publish queued posts directly via Buffer (used when Pinterest is not configured)."""
        update_state("publisher", "publishing", f"Processing up to {limit} queued posts via Buffer")
        try:
            queued_posts = await self.convex.pinterest_list(status="queued", limit=limit)
            if not queued_posts:
                update_state("publisher", "idle", "No queued posts")
                return {"published": 0, "failed": 0, "message": "No queued posts"}

            published_count = 0
            failed_count = 0
            errors = []

            for post in queued_posts:
                post_id = post.get("_id")
                if not post_id:
                    continue
                try:
                    # Lock as processing to prevent scheduler from picking it up again
                    await self.convex.pinterest_mark_processing(post_id)

                    results = await self._post_to_buffer_channels(post)
                    any_success = "pinterest" in results or "twitter" in results
                    if not any_success:
                        raise Exception(
                            f"All Buffer channels failed. Pinterest: {results.get('pinterest_error', 'N/A')}, "
                            f"Twitter: {results.get('twitter_error', 'N/A')}"
                        )

                    await self._safe_mark_published(post_id, f"buffer_{results.get('pinterest', results.get('twitter', 'unknown'))}")
                    published_count += 1
                    logger.info(f"Published post {post_id} via Buffer. Channels: {list(results.keys())}")
                except Exception as e:
                    logger.error(f"Buffer publish failed for {post_id}: {e}")
                    await self.mark_failed(post_id, str(e))
                    errors.append({"post_id": post_id, "error": str(e)})
                    failed_count += 1

            update_state("publisher", "completed", f"Buffer: published {published_count}, failed {failed_count}")
            return {
                "published": published_count,
                "failed": failed_count,
                "message": f"Processed {published_count + failed_count} posts via Buffer",
                "errors": errors if errors else None,
            }
        except Exception as e:
            logger.error(f"Error in _publish_queued_via_buffer: {e}")
            update_state("publisher", "error", str(e))
            return {"published": 0, "failed": 0, "error": str(e)}

    async def _safe_mark_published(self, post_id: str, pin_id: str) -> None:
        """Mark as published in Convex with retry to handle transient failures."""
        published_at = int(time.time() * 1000)
        for attempt in range(3):
            try:
                await self.convex.pinterest_publish(
                    post_id=post_id,
                    pin_id=pin_id,
                    published_at=published_at,
                )
                return
            except Exception as e:
                if attempt == 2:
                    raise
                logger.warning(f"Convex publish update failed (attempt {attempt + 1}), retrying: {e}")
                await asyncio.sleep(1)

    async def _publish_via_buffer(self, post: Dict) -> Optional[str]:
        """Try to publish via Buffer as fallback. Returns primary channel post ID or None."""
        if not self.is_buffer_configured():
            logger.debug("Buffer not configured - skipping fallback")
            return None
        try:
            results = await self._post_to_buffer_channels(post)
            return results.get("pinterest") or results.get("twitter")
        except Exception as e:
            logger.error(f"Buffer fallback failed: {e}")
            return None

    def _get_image_url(self, post: Dict) -> str:
        """Get the best publicly accessible image URL for a post.

        Prefers generatedImageUrl only if it's an absolute public URL;
        otherwise falls back to the original Amazon imageUrl.
        """
        generated = post.get("generatedImageUrl")
        if generated and (generated.startswith("http://") or generated.startswith("https://")):
            return generated
        return post.get("imageUrl", "")

    def is_buffer_configured(self) -> bool:
        """Check if Buffer API credentials are configured."""
        try:
            from pinterest.buffer_client import BufferClient
            return BufferClient().is_configured()
        except Exception:
            return False
    
    async def schedule_post(self, post_id: str, scheduled_at: int) -> None:
        """Update post with scheduled time in Convex."""
        try:
            from convex import ConvexClient
            client = ConvexClient(settings.CONVEX_URL)
            await asyncio.to_thread(client.mutation, "pinterest:updateScheduled", {
                "postId": post_id,
                "scheduledAt": scheduled_at,
            })
        except Exception as e:
            logger.error(f"Failed to schedule post {post_id}: {e}")
    
    async def get_queue_status(self) -> Dict:
        """Get current queue statistics."""
        try:
            stats = await self.convex.pinterest_get_stats()
            return stats
        except Exception as e:
            logger.error(f"Failed to get queue status: {e}")
            return {"total": 0, "queued": 0, "published": 0, "failed": 0}
    
    async def get_posts_by_status(self, status: str, limit: int = 50) -> List[Dict]:
        """Get Pinterest posts filtered by status."""
        try:
            return await self.convex.pinterest_list(status=status, limit=limit)
        except Exception as e:
            logger.error(f"Failed to get posts by status: {e}")
            return []
    
    PLACEHOLDER_TOKENS = frozenset({
        "", "your_pinterest_access_token", "your-pinterest-access-token",
        "your_pinterest_board_id", "your-pinterest-board-id",
    })

    def is_configured(self) -> bool:
        """Check if Pinterest API credentials are configured."""
        if not self.access_token or self.access_token in self.PLACEHOLDER_TOKENS:
            return False
        return True
    
    async def test_connection(self) -> Dict:
        """
        Test Pinterest API connection.
        
        Returns:
            Dict with keys:
                - success: bool
                - message: str
                - boards: list (if successful)
        """
        try:
            api = self.get_api_client()
            boards = await api.get_boards()
            return {
                "success": True,
                "message": f"Connected! Found {len(boards)} boards.",
                "boards": [{"id": b.get("id"), "name": b.get("name")} for b in boards],
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Connection failed: {str(e)}",
                "boards": [],
            }
    
    async def get_boards(self) -> List[Dict]:
        """Get list of Pinterest boards (from Pinterest API when available)."""
        try:
            api = self.get_api_client()
            boards = await api.get_boards()
            return [{"id": b.get("id"), "name": b.get("name")} for b in boards]
        except Exception as e:
            logger.warning(f"Could not fetch boards from Pinterest API: {e}")
            return []

    async def create_board_on_pinterest(self, name: str, description: str = "") -> Optional[str]:
        """Create a board on Pinterest. Returns board ID or None."""
        try:
            api = self.get_api_client()
            board = await api.create_board(name=name, description=description)
            board_id = board.get("id")
            logger.info(f"Created board '{name}' on Pinterest: {board_id}")
            return board_id
        except Exception as e:
            logger.error(f"Failed to create board '{name}' on Pinterest: {e}")
            return None

    async def create_and_register_board(self, name: str, description: str = "") -> Optional[Dict]:
        """Create a board on Pinterest and register it in Convex. Returns board info dict."""
        board_id = await self.create_board_on_pinterest(name, description)
        if board_id:
            try:
                convex_id = await self.convex.pinterest_create_board(name, description)
                return {"id": board_id, "name": name, "convexId": convex_id}
            except Exception:
                return {"id": board_id, "name": name}
        return None

    async def auto_queue_products(self, limit: int = 11) -> Dict:
        """Auto-queue products using round-robin balancing: 3 trending + 2 per source.

        Bucket quotas:
          - trending: 3 (products with trendKeyword, from Pinterest/Amazon trends)
          - bestsellers: 2
          - new_releases: 2
          - movers: 2
          - deals: 2

        Within each bucket, region weighting applies: US 50%, others 50%.
        Products are interleaved in round-robin order for a balanced queue.
        """
        from ai.pin_writer import PinContentAI
        from images.image_generator import PinImageGenerator
        from images.pin_templates import get_board_name_for_category

        QUOTAS = {
            "trending": 3,
            "bestsellers": 2,
            "new_releases": 2,
            "movers": 2,
            "deals": 2,
        }

        SOURCES = ["bestsellers", "new_releases", "movers", "deals"]

        try:
            queued_ids = await self.convex.pinterest_list_all_product_ids()
            trending_ids = set(await self.convex.pinterest_list_trending_product_ids())

            trending_products = await self.convex.products_get_trending(limit=50)
            trending_products = [
                p for p in trending_products
                if p.get("_id") and p.get("_id") not in queued_ids and p.get("_id") in trending_ids
            ]

            by_source: Dict[str, List[Dict]] = {}
            for src in SOURCES:
                products = await self.convex.products_list(source=src, limit=50)
                products = [
                    p for p in products
                    if p.get("_id") and p.get("_id") not in queued_ids and p.get("_id") not in trending_ids
                ]
                by_source[src] = products

            def apply_region_weighting(products: List[Dict], quota: int) -> List[Dict]:
                if not products:
                    return []
                us_products = [p for p in products if self._is_us_region(p)]
                other_products = [p for p in products if not self._is_us_region(p)]
                target_us = max(1, round(quota * 0.5))
                selected = us_products[:target_us] + other_products[:quota - target_us]
                if len(selected) < quota and len(us_products) < target_us:
                    needed = quota - len(selected)
                    selected.extend(other_products[target_us:target_us + needed])
                return selected[:quota]

            trending_selected = apply_region_weighting(trending_products, QUOTAS["trending"])

            source_selected: Dict[str, List[Dict]] = {}
            for src in SOURCES:
                source_selected[src] = apply_region_weighting(by_source[src], QUOTAS[src])

            selected_products: List[Dict] = []
            remaining: Dict[str, List[Dict]] = {
                "trending": trending_selected,
                **{src: source_selected[src] for src in SOURCES},
            }

            for _ in range(QUOTAS["trending"]):
                if remaining["trending"]:
                    selected_products.append(remaining["trending"].pop(0))

            for src in SOURCES:
                for _ in range(QUOTAS[src]):
                    if remaining[src]:
                        selected_products.append(remaining[src].pop(0))

            if not selected_products:
                logger.info("No new products to auto-queue")
                return {"queued": 0, "message": "No new products"}

            content_ai = PinContentAI()
            image_gen = PinImageGenerator()
            errors: List[Dict] = []

            async def _process_one(product: Dict) -> Optional[str]:
                try:
                    content = await asyncio.to_thread(content_ai.generate_content, product)
                    desc = content.get("description", "")
                    tags = content.get("hashtags", [])
                    filename = await image_gen.generate_pin_image(
                        product_image_url=product.get("imageUrl", ""),
                        title=product.get("title", ""),
                        description=desc,
                        hashtags=tags,
                        asin=product.get("asin", ""),
                        category=product.get("category"),
                    )
                    image_url = f"/api/images/{filename}" if filename else None
                    affiliate_url = product.get("affiliateUrl") or f"https://www.amazon.com/dp/{product.get('asin')}?tag={settings.AMAZON_AFFILIATE_TAG}"
                    board_name = get_board_name_for_category(product.get("category"))

                    is_trending = product.get("_id") in trending_ids
                    post_data: Dict[str, Any] = {
                        "productId": product["_id"],
                        "asin": product.get("asin", ""),
                        "imageUrl": product.get("imageUrl", ""),
                        "generatedImageUrl": image_url,
                        "pinTitle": content.get("title", product.get("title", ""))[:100],
                        "pinDescription": content.get("description", ""),
                        "hashtags": content.get("hashtags", []),
                        "affiliateUrl": affiliate_url,
                        "boardName": board_name,
                        "priority": 1,
                    }
                    if is_trending:
                        post_data["trendKeyword"] = product.get("trendKeyword", "trending")
                        post_data["trendTimeframe"] = product.get("trendTimeframe", "daily")

                    post_id = await self.convex.pinterest_queue(post_data)
                    logger.info(f"Auto-queued product {product.get('asin')} → post {post_id} (board: {board_name})")
                    return post_id
                except Exception as e:
                    logger.error(f"Failed to auto-queue {product.get('asin')}: {e}")
                    errors.append({"asin": product.get("asin"), "error": str(e)})
                    return None

            results = await asyncio.gather(*[_process_one(p) for p in selected_products])
            queued_count = sum(1 for r in results if r is not None)

            logger.info(f"Auto-queued {queued_count}/{len(selected_products)} products")
            return {"queued": queued_count, "total": len(selected_products), "errors": errors if errors else None}
        except Exception as e:
            logger.error(f"auto_queue_products failed: {e}")
            return {"queued": 0, "total": 0, "error": str(e)}

    def _is_us_region(self, product: Dict) -> bool:
        """Check if product is likely from US region based on affiliate URL or domain."""
        url = product.get("affiliateUrl", "") or product.get("productUrl", "") or ""
        amazon_domains = ["amazon.com", "amazon.co.uk", "amazon.de", "amazon.fr", "amazon.it", "amazon.es"]
        for domain in amazon_domains:
            if domain in url:
                return domain == "amazon.com"
        category = product.get("category", "")
        return True