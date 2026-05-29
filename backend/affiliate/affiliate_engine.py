"""
Affiliate Link Generator
Generates Amazon affiliate links with proper tracking and validation.
"""

import re
from utils.config import get_settings

class AffiliateEngine:
    def __init__(self, tag: str):
        self.tag = tag or get_settings().AMAZON_AFFILIATE_TAG
    
    def generate_affiliate_link(self, asin: str) -> str:
        """Generate an Amazon affiliate link for a given ASIN."""
        if not self.validate_asin(asin):
            raise ValueError(f"Invalid ASIN format: {asin}")

        base_url = "https://www.amazon.com"
        link = f"{base_url}/dp/{asin}/?tag={self.tag}"
        return link

    def validate_asin(self, asin: str) -> bool:
        """Validate ASIN format."""
        return bool(re.match(r"^[A-Z0-9]{10}$", asin))