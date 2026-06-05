"""
Amazon Product Scraper
Handles scraping of Amazon best sellers, movers & shakers, new releases, and deals.
Uses HTTP requests + BeautifulSoup as primary method, Playwright as fallback.
"""

import httpx
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import asyncio
import random
import re
from dataclasses import dataclass
from utils.config import get_settings
from utils.convex_client import ConvexService
from utils.state import update_state
from affiliate.affiliate_engine import AffiliateEngine
from playwright.async_api import async_playwright
import logging

logger = logging.getLogger(__name__)
settings = get_settings()

@dataclass
class AmazonProduct:
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

class AmazonScraper:
    def __init__(self):
        self.session = httpx.AsyncClient(
            headers={
                "User-Agent": settings.USER_AGENT,
                "Accept-Language": "en-US,en;q=0.9",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            },
            timeout=30,
            follow_redirects=True,
        )
        self.base_url = settings.AMAZON_BASE_URL
    
    async def scrape_all(self) -> List[AmazonProduct]:
        """Scrape products from all Amazon sources."""
        update_state("scraper", "scraping", "Collecting products from Amazon sources")
        products = []
        
        try:
            # Scrape Best Sellers
            update_state("scraper", "scraping", "Scraping Best Sellers")
            bestsellers = await self.scrape_bestsellers()
            for p in bestsellers:
                p.source = "bestsellers"
            products.extend(bestsellers)
            
            await self._random_delay()
            
            # Scrape Movers & Shakers
            update_state("scraper", "scraping", "Scraping Movers & Shakers")
            movers = await self.scrape_movers()
            for p in movers:
                p.source = "movers"
            products.extend(movers)
            
            await self._random_delay()
            
            # Scrape New Releases
            update_state("scraper", "scraping", "Scraping New Releases")
            new_releases = await self.scrape_new_releases()
            for p in new_releases:
                p.source = "new_releases"
            products.extend(new_releases)
            
            await self._random_delay()
            
            # Scrape Deals
            update_state("scraper", "scraping", "Scraping Deals")
            deals = await self.scrape_deals()
            for p in deals:
                p.source = "deals"
            products.extend(deals)
            
            # Remove duplicates by ASIN
            seen = {}
            unique_products = []
            for p in products:
                if p.asin not in seen:
                    seen[p.asin] = p
                    unique_products.append(p)
            
            update_state("scraper", "completed", f"Found {len(unique_products)} products")
            return unique_products
        except Exception as e:
            update_state("scraper", "error", f"Scraping failed: {e}")
            raise
    
    async def scrape_bestsellers(self, category: str = "") -> List[AmazonProduct]:
        """Scrape Amazon Best Sellers."""
        url = f"{self.base_url}/gp/bestsellers/{category}" if category else f"{self.base_url}/gp/bestsellers"
        return await self._scrape_product_list(url, "bestsellers")
    
    async def scrape_movers(self) -> List[AmazonProduct]:
        """Scrape Amazon Movers & Shakers."""
        url = f"{self.base_url}/gp/movers-and-shakers"
        return await self._scrape_product_list(url, "movers")
    
    async def scrape_new_releases(self) -> List[AmazonProduct]:
        """Scrape Amazon New Releases."""
        url = f"{self.base_url}/gp/new-releases"
        return await self._scrape_product_list(url, "new_releases")
    
    async def scrape_deals(self) -> List[AmazonProduct]:
        """Scrape Amazon Deals."""
        url = f"{self.base_url}/gp/goldbox"
        return await self._scrape_product_list(url, "deals")
    
    async def _scrape_product_list(self, url: str, source: str) -> List[AmazonProduct]:
        """Generic scraper for Amazon product list pages."""
        try:
            response = await self.session.get(url)
            if response.status_code != 200:
                return await self._scrape_with_playwright(url, source)
            
            soup = BeautifulSoup(response.text, "lxml")
            products = self._parse_product_grid(soup, source)
            if not products:
                products = await self._scrape_with_playwright(url, source)
            return products
        except Exception:
            return await self._scrape_with_playwright(url, source)
    
    def _parse_product_grid(self, soup: BeautifulSoup, source: str) -> List[AmazonProduct]:
        """Parse product grid HTML into structured product data."""
        products = []
        
        # Find all product containers by data-asin attribute (current Amazon HTML structure)
        items = soup.find_all("div", attrs={"data-asin": True}) or \
                soup.find_all("li", class_=re.compile("a-carousel-card"))
        
        for item in items[:20]:  # Limit to top 20
            try:
                product = self._parse_product_item(item, source)
                if product:
                    products.append(product)
            except Exception:
                continue
        
        return products
    
    def _parse_product_item(self, item, source: str) -> Optional[AmazonProduct]:
        """Parse a single product item."""
        try:
            asin = item.get("data-asin")
            if not asin:
                link_elem = item.find("a", href=True)
                if link_elem:
                    match = re.search(r"/dp/([A-Z0-9]{10})", link_elem["href"])
                    if match:
                        asin = match.group(1)
            if not asin:
                return None
            asin = asin.strip()
            
            title = ""
            title_elem = item.find("div", class_=re.compile("p13n-sc-truncate")) or \
                        item.find("span", class_=re.compile("a-size-base|a-size-medium|a-text-normal")) or \
                        item.find("img", alt=True)
            if title_elem:
                title = title_elem.get("alt", "").strip() if title_elem.name == "img" else title_elem.text.strip()
            if not title:
                link = item.find("a", class_=re.compile("a-link-normal"))
                if link and link.get("title"):
                    title = link["title"].strip()
            if not title:
                title = "Unknown Product"
            
            price_elem = item.find("span", class_=re.compile("p13n-sc-price"))
            price = None
            if price_elem:
                price_text = re.sub(r"[^\d.]", "", price_elem.text)
                if price_text:
                    try:
                        price = float(price_text)
                    except ValueError:
                        pass
            
            rating_elem = item.find("span", class_=re.compile("a-icon-alt"))
            rating = None
            if rating_elem:
                rating_match = re.search(r"([\d.]+) out of 5", rating_elem.text)
                if rating_match:
                    rating = float(rating_match.group(1))
            
            review_elem = item.find("span", class_=re.compile("a-size-small"))
            review_count = None
            if review_elem:
                review_match = re.search(r"([\d,]+)", review_elem.text)
                if review_match:
                    try:
                        review_count = int(review_match.group(1).replace(",", ""))
                    except ValueError:
                        pass
            
            img_elem = item.find("img")
            image_url = img_elem.get("src") if img_elem else None
            
            product_url = f"{settings.AMAZON_BASE_URL}/dp/{asin}"
            
            return AmazonProduct(
                asin=asin,
                title=title,
                price=price,
                rating=rating,
                review_count=review_count,
                image_url=image_url,
                product_url=product_url,
                source=source,
            )
        except Exception:
            return None
    
    async def _scrape_with_playwright(self, url: str, source: str) -> List[AmazonProduct]:
        """Fallback scraper using Playwright for JavaScript-rendered pages."""
        products = []
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page(user_agent=settings.USER_AGENT)
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(random.uniform(2, 5))
                
                content = await page.content()
                soup = BeautifulSoup(content, "lxml")
                products = self._parse_product_grid(soup, source)
                
                await browser.close()
        except Exception:
            pass
        return products
    
    async def _random_delay(self):
        """Random delay between requests."""
        await asyncio.sleep(random.uniform(settings.SCRAPE_DELAY_MIN, settings.SCRAPE_DELAY_MAX))
    
    async def store_products_to_convex(self, products: List[AmazonProduct]) -> int:
        """Store scraped products to Convex DB."""
        if not products:
            return 0
        
        update_state("scraper", "scraping", f"Storing {len(products)} products to database")
        convex = ConvexService()
        stored_count = 0
        
        aff_engine = AffiliateEngine()
        for product in products:
            try:
                product_url = f"{settings.AMAZON_BASE_URL}/dp/{product.asin}"
                affiliate_url = aff_engine.generate_affiliate_link(product.asin)
                data = {
                    "asin": product.asin,
                    "title": product.title,
                    "source": product.source or "unknown",
                    "productUrl": product_url,
                    "affiliateUrl": affiliate_url,
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
                await convex.products_upsert(data)
                stored_count += 1
            except Exception as e:
                logger.error(f"Failed to store product {product.asin}: {e}")
                continue
        
        update_state("scraper", "completed", f"Stored {stored_count} products")
        return stored_count
    
    async def get_stored_products(self, source: Optional[str] = None, min_score: Optional[float] = None, limit: int = 50) -> List[AmazonProduct]:
        """Retrieve stored products from Convex DB."""
        try:
            convex = ConvexService()
            products_data = await convex.products_list(source=source, min_score=min_score, limit=limit)
            
            products = []
            for p in products_data:
                products.append(AmazonProduct(
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
                    source=p.get("source", ""),
                ))
            return products
        except Exception as e:
            logger.error(f"Failed to get stored products: {e}")
            return []
    
    async def get_scraping_status(self) -> Dict:
        """Get the status of the most recent scraping operation from Convex."""
        try:
            convex = ConvexService()
            recent_logs = await convex.scraping_logs_get_recent(limit=1)
            
            if recent_logs:
                last_log = recent_logs[0]
                return {
                    "status": last_log.get("status", "unknown"),
                    "last_run": last_log.get("startedAt"),
                    "products_found": last_log.get("productsFound", 0),
                    "source": last_log.get("source", ""),
                }
            return {"status": "no_runs", "last_run": None, "products_found": 0}
        except Exception as e:
            logger.error(f"Failed to get scraping status: {e}")
            return {"status": "error", "last_run": None, "products_found": 0, "error": str(e)}
