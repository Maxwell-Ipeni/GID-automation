"""
Pin Content Generator
Generates optimized titles and descriptions for Pinterest affiliate pins.
"""

from typing import Optional, Dict, Any
import random


def generate_pin_content(
    title: str,
    affiliate_url: str,
    product_image_url: str,
    category: Optional[str] = None,
    rating: Optional[float] = None,
    price: Optional[float] = None,
    review_count: Optional[int] = None,
) -> Dict[str, str]:
    """
    Generate optimized pin title and description for affiliate marketing.
    
    Args:
        title: Product title from Amazon
        affiliate_url: Full affiliate link with tracking tag
        product_image_url: Product image URL from Amazon
        category: Product category (optional)
        rating: Product rating out of 5 (optional)
        price: Product price (optional)
        review_count: Number of reviews (optional)
    
    Returns:
        Dict with keys:
            - title: Optimized pin title
            - description: SEO-friendly description with hashtags
            - link: Affiliate link
    """
    # Generate title
    pin_title = _generate_title(
        title=title,
        rating=rating,
        price=price,
    )
    
    # Generate description
    pin_description = _generate_description(
        title=title,
        category=category,
        rating=rating,
        price=price,
        review_count=review_count,
    )
    
    return {
        "title": pin_title,
        "description": pin_description,
        "link": affiliate_url,
    }


def _generate_title(
    title: str,
    rating: Optional[float] = None,
    price: Optional[float] = None,
) -> str:
    """
    Generate click-worthy pin title.
    
    Format: {Product Name} - ⭐{rating}/5 | ${price}
    Example: "Wireless Earbuds Pro - ⭐4.5/5 | $29.99"
    """
    # Truncate title if too long (leaving room for rating/price)
    max_title_len = 60
    if len(title) > max_title_len:
        title = title[:max_title_len].rsplit(" ", 1)[0] + "..."
    
    parts = [title]
    
    # Add rating if available
    if rating is not None and rating > 0:
        parts.append(f"⭐ {rating:.1f}/5")
    
    # Add price if available
    if price is not None and price > 0:
        parts.append(f"${price:.2f}")
    
    return " | ".join(parts)


def _generate_description(
    title: str,
    category: Optional[str] = None,
    rating: Optional[float] = None,
    price: Optional[float] = None,
    review_count: Optional[int] = None,
) -> str:
    """
    Generate SEO-optimized description with hashtags.
    
    Structure:
    1. Hook line
    2. Key features (rating, reviews, price)
    3. CTA
    4. Relevant hashtags
    """
    lines = []
    
    # Hook - extract key word from title
    title_word = _extract_first_meaningful_word(title)
    if title_word:
        lines.append(f"Check out this {title_word} on Amazon!")
    else:
        lines.append("Check out this amazing product on Amazon!")
    
    lines.append("")
    
    # Features
    if rating is not None and rating > 0:
        lines.append(f"⭐ {rating:.1f} star rating")
    
    if review_count is not None and review_count > 0:
        formatted_reviews = _format_count(review_count)
        lines.append(f"📝 {formatted_reviews} customer reviews")
    
    if price is not None and price > 0:
        lines.append(f"💰 Current price: ${price:.2f}")
    
    lines.append("")
    
    # CTA
    lines.append("Link in bio 🔗")
    lines.append("Use my affiliate link to shop ⬆️")
    
    lines.append("")
    
    # Hashtags
    hashtags = _generate_hashtags(category, title)
    lines.append(hashtags)
    
    return "\n".join(lines)


def _extract_first_meaningful_word(title: str) -> str:
    """Extract the first meaningful word from a product title."""
    # Skip common non-meaningful words
    skip_words = {"the", "a", "an", "for", "with", "and", "of", "to", "in", "on"}
    
    words = title.split()
    for word in words:
        clean_word = word.strip("-,:").lower()
        if clean_word and clean_word not in skip_words and len(clean_word) > 2:
            # Capitalize for display
            return clean_word.capitalize()
    
    return ""


def _format_count(count: int) -> str:
    """Format review count for display."""
    if count >= 1000000:
        return f"{count/1000000:.1f}M"
    elif count >= 1000:
        return f"{count/1000:.1f}K"
    else:
        return str(count)


def _generate_hashtags(category: Optional[str] = None, title: str = "") -> str:
    """
    Generate relevant hashtags for the pin.
    
    Structure:
    - 2-3 general affiliate/shopping tags
    - 2-3 category-specific tags
    - 1-2 product type tags
    """
    tags = []
    
    # General affiliate tags (always included)
    tags.extend([
        "#affiliatelink",
        "#amazonfinds",
        "#shopsmall",
    ])
    
    # Category-specific tags
    if category:
        category_clean = _clean_for_hashtag(category)
        if category_clean:
            tags.append(f"#{category_clean}")
            tags.append(f"#{category_clean}deals")
    
    # Add tags based on title keywords
    title_keywords = _extract_keywords(title)
    for keyword in title_keywords[:2]:
        hashtag = f"#{keyword}"
        if hashtag not in tags:
            tags.append(hashtag)
    
    # Limit to 8-10 total hashtags
    tags = tags[:10]
    
    return " ".join(tags)


def _clean_for_hashtag(text: str) -> str:
    """Convert text to valid hashtag format."""
    # Remove special characters, keep letters and numbers
    clean = "".join(c for c in text if c.isalnum() or c.isspace())
    # Convert spaces to camelCase-ish
    words = clean.split()
    if not words:
        return ""
    result = "".join(w.capitalize() for w in words)
    return result[:30]  # Limit length


def _extract_keywords(title: str) -> list:
    """Extract potential keyword hashtags from title."""
    # Words to skip in hashtags
    skip_words = {
        "the", "a", "an", "for", "with", "and", "of", "to", "in", "on",
        "for", "from", "this", "that", "with", "your", "its", "best",
        "top", "new", "latest", "popular", "free", "sale", "deal",
    }
    
    # Common product types to extract
    product_types = {
        "earbuds", "headphones", "charger", "cable", "case", "cover",
        "speaker", "keyboard", "mouse", "watch", "band", "ring", "light",
        "camera", "speaker", "stand", "mount", "holder", "bag", "case",
    }
    
    words = title.lower().split()
    keywords = []
    
    for word in words:
        clean = "".join(c for c in word if c.isalnum())
        if (clean not in skip_words and len(clean) > 3 and clean not in keywords):
            # Check if it's a known product type
            if clean in product_types:
                keywords.insert(0, clean)  # Prioritize product types
            else:
                keywords.append(clean)
    
    return keywords[:4]


def get_pin_title_variations(
    title: str,
    rating: Optional[float] = None,
    price: Optional[float] = None,
) -> list:
    """
    Generate multiple title variations for A/B testing.
    
    Returns 3 variations with different formatting.
    """
    variations = []
    
    # Variation 1: Standard with rating and price
    variations.append(_generate_title(title, rating, price))
    
    # Variation 2: Compact - just title and discount indication
    if price and price > 0:
        variations.append(f"{title[:50]}... - 🔥 Great Deal")
    else:
        variations.append(f"{title[:60]}...")
    
    # Variation 3: Value-focused
    if rating and rating >= 4.0:
        rating_note = f"{rating:.1f}⭐ Rated"
        if price:
            rating_note += f" | ${price:.2f}"
        variations.append(f"{title[:40]}... | {rating_note}")
    else:
        variations.append(_generate_title(title, None, price))
    
    return variations[:3]


def get_description_template() -> str:
    """
    Get a template for manual description writing.
    Useful for UI where user wants to customize.
    """
    return """Check out this product on Amazon!

⭐ [RATING] star rating
📝 [REVIEW_COUNT] customer reviews
💰 [PRICE]

Link in bio 🔗
Use my affiliate link to shop ⬆️

#affiliate #amazonfinds #shopsmall #[CATEGORY] #[PRODUCTTYPE]"""