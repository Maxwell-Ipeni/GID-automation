"""
Amazon Trend Discovery Service
Scrapes Amazon's trending signals (Movers & Shakers, New Releases, etc.)
from multiple regions (US, UK, DE, FR, IT, ES) to discover trending products.
"""

import re
import random
import logging
import asyncio
from typing import Dict, List, Optional, Set
from bs4 import BeautifulSoup
import httpx
from dataclasses import dataclass

logger = logging.getLogger(__name__)

TRENDING_SOURCES = [
    {"name": "movers_shakers", "url": "/gp/movers-and-shakers"},
    {"name": "new_releases", "url": "/gp/new-releases"},
]

REGION_LABELS = {
    "us": "US",
    "uk": "UK",
    "de": "DE",
    "fr": "FR",
    "it": "IT",
    "es": "ES",
}


@dataclass
class DiscoveredASIN:
    asin: str
    source: str
    keyword: str
    region: str


class AmazonTrendService:
    def __init__(self):
        from utils.config import get_settings, AMAZON_REGIONS
        self.settings = get_settings()
        self.regions = AMAZON_REGIONS
        self.session = httpx.AsyncClient(
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                              "AppleWebKit/537.36 (KHTML, like Gecko) "
                              "Chrome/120.0.0.0 Safari/537.36",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            },
            timeout=30,
            follow_redirects=True,
        )

    async def discover_trending_asins(self) -> List[DiscoveredASIN]:
        discovered: List[DiscoveredASIN] = []
        seen_global: Set[str] = set()

        for region_code, region_info in self.regions.items():
            base_url = region_info["base_url"]
            label = REGION_LABELS.get(region_code, region_code.upper())
            logger.info(f"AmazonTrendService: scraping region {label} ({base_url})")

            region_seen: Set[str] = set()
            for source in TRENDING_SOURCES:
                try:
                    asins = await self._scrape_trending_page(
                        base_url, source["url"], source["name"], label
                    )
                    for asin in asins:
                        unique_key = f"{asin}:{region_code}"
                        if unique_key not in seen_global:
                            seen_global.add(unique_key)
                            region_seen.add(asin)
                            discovered.append(DiscoveredASIN(
                                asin=asin,
                                source=source["name"],
                                keyword=f"{source['name'].replace('_', ' ').title()} {label}",
                                region=region_code,
                            ))
                    await asyncio.sleep(random.uniform(2.0, 4.0))
                except Exception as e:
                    logger.error(f"Failed to scrape {source['name']} for {label}: {e}")

            if region_seen:
                logger.info(f"  {label}: found {len(region_seen)} ASINs")

        logger.info(
            f"AmazonTrendService: total {len(discovered)} ASINs across all regions"
        )
        return discovered

    async def _scrape_trending_page(self, base_url: str, path: str, source: str, label: str) -> List[str]:
        url = f"{base_url}{path}"
        asins: Set[str] = set()

        try:
            response = await self.session.get(url)
            if response.status_code != 200:
                logger.warning(f"{source} ({label}): HTTP {response.status_code}")
                return []

            soup = BeautifulSoup(response.text, "lxml")

            for div in soup.select("[data-asin]"):
                asin = div.get("data-asin", "").strip()
                if re.match(r"^[A-Z0-9]{10}$", asin):
                    asins.add(asin)

            for link in soup.select("a[href*='/dp/']"):
                href = link.get("href", "")
                match = re.search(r"/dp/([A-Z0-9]{10})", href)
                if match:
                    asins.add(match.group(1))

            result = list(asins)[:30]
            if result:
                logger.info(f"{source} ({label}): found {len(result)} ASINs")
            return result
        except Exception as e:
            logger.error(f"Failed to scrape {source} ({label}): {e}")
            return []

    async def fetch_and_process(self) -> Dict:
        discovered = await self.discover_trending_asins()
        if not discovered:
            return {"keywords": [], "asins": [], "count": 0}

        all_asins = list({d.asin for d in discovered})

        keyword_map: Dict[str, List[str]] = {}
        region_keyword_map: Dict[str, Dict[str, List[str]]] = {}
        for d in discovered:
            if d.keyword not in keyword_map:
                keyword_map[d.keyword] = []
            keyword_map[d.keyword].append(d.asin)

            if d.region not in region_keyword_map:
                region_keyword_map[d.region] = {}
            if d.keyword not in region_keyword_map[d.region]:
                region_keyword_map[d.region][d.keyword] = []
            region_keyword_map[d.region][d.keyword].append(d.asin)

        return {
            "keywords": list(keyword_map.keys()),
            "keyword_asins": keyword_map,
            "region_keyword_asins": region_keyword_map,
            "asins": all_asins,
            "regions": list(self.regions.keys()),
            "count": len(all_asins),
        }

    async def close(self):
        await self.session.aclose()
