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
from playwright.async_api import async_playwright

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
        products = []
        
        # Scrape Best Sellers
        bestsellers = await self.scrape_bestsellers()
        for p in bestsellers:
            p.source = "bestsellers"
        products.extend(bestsellers)
        
        await self._random_delay()
        
        # Scrape Movers & Shakers
        movers = await self.scrape_movers()
        for p in movers:
            p.source = "movers"
        products.extend(movers)
        
        await self._random_delay()
        
        # Scrape New Releases
        new_releases = await self.scrape_new_releases()
        for p in new_releases:
            p.source = "new_releases"
        products.extend(new_releases)
        
        await self._random_delay()
        
        # Scrape Deals
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
        
        return unique_products
    
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
                # Fallback to Playwright if blocked
                return await self._scrape_with_playwright(url, source)
            
            soup = BeautifulSoup(response.text, "lxml")
            return self._parse_product_grid(soup, source)
        except Exception:
            # Fallback to Playwright on any error
            return await self._scrape_with_playwright(url, source)
    
    def _parse_product_grid(self, soup: BeautifulSoup, source: str) -> List[AmazonProduct]:
        """Parse product grid from BeautifulSoup."""
        products = []
        
        # Try multiple selector patterns since Amazon changes frequently
        items = soup.find_all("div", class_=re.compile("zg-grid-general-faceout")) or \
                soup.find_all("div", class_=re.compile("a-section a-spacing-medium")) or \
                soup.find_all("li", class_=re.compile("zg-item-immersion"))
        
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
            # Extract ASIN from data attribute or href
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
            
            # Extract title
            title_elem = item.find("span", class_=re.compile("a-size-medium|a-size-base")) or \
                        item.find("div", class_=re.compile("p13n-sc-truncate"))
            title = title_elem.text.strip() if title_elem else "Unknown Product"
            
            # Extract price
            price_elem = item.find("span", class_=re.compile("a-price")) or \
                        item.find("span", class_=re.compile("p13n-sc-price"))
            price = None
            if price_elem:
                price_text = price_elem.text.replace("$", "").replace(",", "")
                try:
                    price = float(price_text)
                except ValueError:
                    pass
            
            # Extract rating
            rating_elem = item.find("span", class_=re.compile("a-icon-alt"))
            rating = None
            if rating_elem:
                rating_match = re.search(r"([\d.]+) out of 5", rating_elem.text)
                if rating_match:
                    rating = float(rating_match.group(1))
            
            # Extract review count
            review_elem = item.find("span", class_=re.compile("a-size-small")) or \
                         item.find("a", class_=re.compile("a-link-normal.*a-text-normal"))
            review_count = None
            if review_elem:
                review_match = re.search(r"([\d,]+)", review_elem.text.replace(",", ""))
                if review_match:
                    try:
                        review_count = int(review_match.group(1))
                    except ValueError:
                        pass
            
            # Extract image URL
            img_elem = item.find("img")
            image_url = img_elem.get("src") if img_elem else None
            
            # Build product URL
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
    
    async def get_stored_products(self, source: Optional[str] = None, min_score: Optional[float] = None, limit: int = 50) -> List[AmazonProduct]:
        """Retrieve stored products from the database."""
        # This is a simplified version - in production, this would query Convex DB
        return []
    
    async def get_scraping_status(self) -> Dict:
        """Get the status of the most recent scraping operation."""
        # Simplified - in production, this would query the database
        return {"status": "unknown", "last_run": None, "products_found": 0}
