"""
Scheduler for scraping Amazon products
"""

import asyncio
from datetime import datetime
from typing import Dict
from scraping.amazon_scraper import AmazonScraper

class ScraperScheduler:
    def __init__(self, scraper: AmazonScraper):
        self.scraper = scraper
        self.is_running = False
    
    async def run(self):
        """Run the scraping scheduler."""
        self.is_running = True
        try:
            results = await self.scraper.scrape_all()
            return {
                "status": "completed",
                "timestamp": datetime.now().isoformat(),
                "products_found": len(results)
            }
        except Exception as e:
            return {
                "status": "error",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
        finally:
            self.is_running = False