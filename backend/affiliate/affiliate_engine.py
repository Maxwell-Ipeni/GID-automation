"""
Affiliate Link Generator
Generates Amazon affiliate links with proper tracking and validation.
"""

import re
import logging
from typing import Optional
from utils.config import get_settings
from utils.convex_client import ConvexService

logger = logging.getLogger(__name__)


class AffiliateEngine:
    def __init__(self, tag: Optional[str] = None):
        self.tag = tag or get_settings().AMAZON_AFFILIATE_TAG
    
    def generate_affiliate_link(self, asin: str) -> str:
        """Generate an Amazon affiliate link for a given ASIN."""
        if not self.validate_asin(asin):
            raise ValueError(f"Invalid ASIN format: {asin}")

        return f"https://www.amazon.com/dp/{asin}?tag={self.tag}"
    
    def generate_for_product(self, asin: str, product_url: str, product_title: str = "") -> dict:
        """
        Generate affiliate link data for a product.
        Returns dict with link details.
        """
        affiliate_url = self.generate_affiliate_link(asin)
        return {
            "asin": asin,
            "affiliateUrl": affiliate_url,
            "productUrl": product_url,
            "title": product_title,
        }
    
    async def store_affiliate_link(self, asin: str) -> Optional[dict]:
        """
        Generate an affiliate link and store it in Convex.
        Returns the stored link data or None if product not found in Convex.
        """
        try:
            convex = ConvexService()
            
            products = await convex.products_list(source=None, min_score=None, limit=100)
            product = None
            for p in products:
                if p.get("asin") == asin:
                    product = p
                    break
            
            if not product:
                logger.warning(f"Product with ASIN {asin} not found in Convex")
                return None
            
            product_id = product.get("_id")
            if not product_id:
                logger.error(f"Product {asin} has no _id")
                return None
            
            result = await convex.affiliate_generate(
                product_id=product_id,
                asin=asin,
                affiliate_tag=self.tag
            )
            
            affiliate_url = self.generate_affiliate_link(asin)
            
            return {
                "asin": asin,
                "affiliateUrl": affiliate_url,
                "productId": product_id,
                "stored": True,
            }
        except Exception as e:
            logger.error(f"Failed to store affiliate link for {asin}: {e}")
            return None
    
    def validate_asin(self, asin: str) -> bool:
        """Validate ASIN format."""
        if not asin:
            return False
        return bool(re.match(r"^[A-Z0-9]{10}$", asin.upper()))