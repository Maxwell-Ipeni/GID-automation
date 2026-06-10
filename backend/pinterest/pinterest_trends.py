"""
Pinterest Trend Service
Fetches trending keywords from Pinterest API across multiple regions,
extracts Amazon ASINs from pin links, cross-references with the product DB,
queues matched products as priority, and discovers new ASINs via Amazon scrape.
"""

import re
import asyncio
import logging
from typing import Dict, List, Optional, Set, Tuple
from utils.config import get_settings, PINTEREST_REGIONS, AMAZON_PINTEREST_MAP, domain_for_region, base_url_for_region
from utils.convex_client import ConvexService
from pinterest.api_client import PinterestApiClient
from scraping.amazon_scraper import AmazonScraper

logger = logging.getLogger(__name__)


AMAZON_URL_PATTERNS = [
    r"/dp/([A-Z0-9]{10})",
    r"/gp/product/([A-Z0-9]{10})",
    r"/exec/obidos/ASIN/([A-Z0-9]{10})",
    r"\?ASIN=([A-Z0-9]{10})",
    r"/product/([A-Z0-9]{10})",
    r"/dp/product/([A-Z0-9]{10})",
]


class PinterestTrendService:
    _ai_semaphore = asyncio.Semaphore(2)

    def __init__(
        self,
        api_client: Optional[PinterestApiClient] = None,
        convex: Optional[ConvexService] = None,
        scraper: Optional[AmazonScraper] = None,
    ):
        self._api_client = api_client
        self._convex = convex
        self._scraper = scraper
        self.settings = get_settings()

    @property
    def api_client(self) -> PinterestApiClient:
        if self._api_client is None:
            self._api_client = PinterestApiClient()
        return self._api_client

    @property
    def convex(self) -> ConvexService:
        if self._convex is None:
            self._convex = ConvexService()
        return self._convex

    @property
    def scraper(self) -> AmazonScraper:
        if self._scraper is None:
            self._scraper = AmazonScraper()
        return self._scraper

    def extract_asins(self, pins: List[Dict]) -> List[str]:
        asins: Set[str] = set()
        for pin in pins:
            link = pin.get("link", "") or ""
            for pattern in AMAZON_URL_PATTERNS:
                match = re.search(pattern, link)
                if match:
                    asins.add(match.group(1))
                    break
        return list(asins)

    async def cross_reference(self, asins: List[str]) -> Tuple[List[str], List[str]]:
        if not asins:
            return [], []

        existing_products = await self.convex.products_list_by_asins(asins)
        existing_asins = {p.get("asin", "") for p in existing_products if p.get("asin")}

        existing = [a for a in asins if a in existing_asins]
        new_asins = [a for a in asins if a not in existing_asins]
        return existing, new_asins

    async def queue_matched(
        self,
        asins: List[str],
        trend_keyword: str,
        timeframe: str,
    ) -> int:
        if not asins:
            return 0

        from ai.pin_writer import PinContentAI
        from images.image_generator import PinImageGenerator
        from images.pin_templates import get_board_name_for_category

        region_code = "us"
        for suffix in ["_us", "_uk", "_de", "_fr", "_it", "_es"]:
            if timeframe.endswith(suffix):
                region_code = suffix[1:]
                break

        existing_products = await self.convex.products_list_by_asins(asins)
        already_queued = await self.convex.pinterest_list_all_product_ids()
        content_ai = PinContentAI()
        image_gen = PinImageGenerator()
        amazon_domain = domain_for_region(region_code)
        amazon_base = base_url_for_region(region_code)

        queued_count = 0
        for product in existing_products:
            pid = product.get("_id")
            if not pid or pid in already_queued:
                continue

            try:
                async with self._ai_semaphore:
                    content = await asyncio.to_thread(
                        content_ai.generate_content, product
                    )
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
                affiliate_url = f"https://www.amazon.{amazon_domain}/dp/{product.get('asin')}?tag={self.settings.AMAZON_AFFILIATE_TAG}"
                board_name = get_board_name_for_category(product.get("category"))

                post_data = {
                    "productId": pid,
                    "asin": product.get("asin", ""),
                    "imageUrl": product.get("imageUrl", ""),
                    "pinTitle": content.get("title", product.get("title", ""))[:100],
                    "pinDescription": desc,
                    "hashtags": tags,
                    "affiliateUrl": affiliate_url,
                    "boardName": board_name,
                    "priority": 1,
                    "trendKeyword": trend_keyword,
                    "trendTimeframe": timeframe,
                }
                if image_url:
                    post_data["generatedImageUrl"] = image_url
                await self.convex.pinterest_queue(post_data)
                queued_count += 1
                logger.info(
                    f"Trend queued (matched): {product.get('asin')} "
                    f"(keyword: {trend_keyword})"
                )
            except Exception as e:
                logger.error(
                    f"Failed to queue matched {product.get('asin')}: {e}"
                )

        return queued_count

    async def scrape_and_queue_new(
        self,
        asins: List[str],
        trend_keyword: str,
        timeframe: str,
    ) -> int:
        if not asins:
            return 0

        from ai.pin_writer import PinContentAI
        from images.image_generator import PinImageGenerator
        from images.pin_templates import get_board_name_for_category

        region_code = "us"
        for suffix in ["_us", "_uk", "_de", "_fr", "_it", "_es"]:
            if timeframe.endswith(suffix):
                region_code = suffix[1:]
                break

        scraped = await self.scraper.scrape_by_asins(asins)
        if not scraped:
            logger.warning(f"No products scraped for trend '{trend_keyword}'")
            return 0

        stored_asins = await self.scraper.store_products_to_convex(scraped)
        if not stored_asins:
            return 0

        stored_asins_set = set()
        for p in scraped:
            if p.asin:
                stored_asins_set.add(p.asin)

        stored_products = await self.convex.products_list_by_asins(list(stored_asins_set))
        already_queued = await self.convex.pinterest_list_all_product_ids()
        content_ai = PinContentAI()
        image_gen = PinImageGenerator()
        amazon_domain = domain_for_region(region_code)

        queued_count = 0
        for product in stored_products:
            pid = product.get("_id")
            if not pid or pid in already_queued:
                continue

            try:
                async with self._ai_semaphore:
                    content = await asyncio.to_thread(
                        content_ai.generate_content, product
                    )
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
                affiliate_url = f"https://www.amazon.{amazon_domain}/dp/{product.get('asin')}?tag={self.settings.AMAZON_AFFILIATE_TAG}"
                board_name = get_board_name_for_category(product.get("category"))

                post_data = {
                    "productId": pid,
                    "asin": product.get("asin", ""),
                    "imageUrl": product.get("imageUrl", ""),
                    "pinTitle": content.get("title", product.get("title", ""))[:100],
                    "pinDescription": desc,
                    "hashtags": tags,
                    "affiliateUrl": affiliate_url,
                    "boardName": board_name,
                    "priority": 1,
                    "trendKeyword": trend_keyword,
                    "trendTimeframe": timeframe,
                }
                if image_url:
                    post_data["generatedImageUrl"] = image_url
                await self.convex.pinterest_queue(post_data)
                queued_count += 1
                logger.info(
                    f"Trend queued (new): {product.get('asin')} "
                    f"(keyword: {trend_keyword})"
                )
            except Exception as e:
                logger.error(
                    f"Failed to queue new {product.get('asin')}: {e}"
                )

        return queued_count

    async def save_trend_results(
        self,
        keyword: str,
        rank: int,
        source: str,
        timeframe: str,
        matched_asins: List[str],
        discovered_asins: List[str],
        queued_count: int,
    ) -> None:
        total_products = len(matched_asins) + len(discovered_asins)
        try:
            await self.convex.pinterest_trends_save(
                keyword=keyword,
                rank=rank,
                source=source,
                timeframe=timeframe,
                matchedAsins=matched_asins,
                discoveredAsins=discovered_asins,
                productCount=total_products,
                queuedCount=queued_count,
            )
        except Exception as e:
            logger.error(f"Failed to save trend result '{keyword}': {e}")

    async def fetch_and_process(self, timeframe: str = "today", region: str = "US") -> Dict:
        logger.info(f"PinterestTrendService: fetching {timeframe} trends for region {region}")

        region_code = AMAZON_PINTEREST_MAP.get(region, "us")
        region_timeframe = f"{timeframe}_{region_code}"

        try:
            keywords = await self.api_client.get_trending_keywords(
                region=region, date_range=timeframe
            )
        except Exception as e:
            logger.error(f"Failed to fetch Pinterest trends ({timeframe}/{region}): {e}")
            return {
                "timeframe": region_timeframe,
                "region": region,
                "error": str(e),
                "keywords_found": 0,
                "total_asins": 0,
                "matched": 0,
                "discovered": 0,
                "queued": 0,
            }

        if not keywords:
            logger.info(f"No Pinterest trends for {timeframe}/{region}")
            return {
                "timeframe": region_timeframe,
                "region": region,
                "keywords_found": 0,
                "total_asins": 0,
                "matched": 0,
                "discovered": 0,
                "queued": 0,
            }

        all_asins: Set[str] = set()
        keyword_results: List[Dict] = []
        total_matched = 0
        total_discovered = 0
        total_queued = 0

        for kw_entry in keywords[:15]:
            keyword = kw_entry.get("keyword", "")
            rank = kw_entry.get("rank", 0)
            if not keyword:
                continue

            try:
                pins = await self.api_client.search_pins(keyword, limit=25)
                asins = self.extract_asins(pins)

                if not asins:
                    logger.debug(f"No Amazon ASINs found for '{keyword}' ({region})")
                    await self.save_trend_results(
                        keyword=keyword,
                        rank=rank,
                        source="pinterest",
                        timeframe=region_timeframe,
                        matched_asins=[],
                        discovered_asins=[],
                        queued_count=0,
                    )
                    keyword_results.append({
                        "keyword": keyword,
                        "rank": rank,
                        "asins": [],
                        "matched": 0,
                        "discovered": 0,
                        "queued": 0,
                    })
                    continue

                existing, new_asins = await self.cross_reference(asins)
                all_asins.update(asins)

                matched_count = 0
                discovered_count = 0
                queued_for_keyword = 0

                if existing:
                    matched_count = await self.queue_matched(
                        existing, keyword, region_timeframe
                    )
                    queued_for_keyword += matched_count

                if new_asins:
                    discovered_count = await self.scrape_and_queue_new(
                        new_asins, keyword, region_timeframe
                    )
                    queued_for_keyword += discovered_count

                total_matched += matched_count
                total_discovered += discovered_count
                total_queued += queued_for_keyword

                await self.save_trend_results(
                    keyword=keyword,
                    rank=rank,
                    source="pinterest",
                    timeframe=region_timeframe,
                    matched_asins=existing,
                    discovered_asins=new_asins,
                    queued_count=queued_for_keyword,
                )

                keyword_results.append({
                    "keyword": keyword,
                    "rank": rank,
                    "asins": asins,
                    "matched": matched_count,
                    "discovered": discovered_count,
                    "queued": queued_for_keyword,
                })

                logger.info(
                    f"Trend '{keyword}' ({region}, {timeframe}): "
                    f"{len(asins)} ASINs, "
                    f"{matched_count} matched, "
                    f"{discovered_count} new, "
                    f"{queued_for_keyword} queued"
                )

            except Exception as e:
                logger.error(f"Error processing trend keyword '{keyword}' ({region}): {e}")
                continue

        return {
            "timeframe": region_timeframe,
            "region": region,
            "keywords_found": len(keywords),
            "keywords_processed": len(keyword_results),
            "total_asins": len(all_asins),
            "matched": total_matched,
            "discovered": total_discovered,
            "queued": total_queued,
            "keywords": keyword_results,
        }

    async def run_all_regions(self, timeframe: str = "today") -> List[Dict]:
        tasks = [
            self.fetch_and_process(timeframe=timeframe, region=region)
            for region in PINTEREST_REGIONS
        ]
        return await asyncio.gather(*tasks)
