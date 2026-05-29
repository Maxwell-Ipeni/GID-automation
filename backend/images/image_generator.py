"""
Image Processing Module
Handles downloading product images, resizing, and generating Pinterest pin layouts.
"""

from PIL import Image, ImageDraw, ImageFont
import httpx
from io import BytesIO
from typing import Optional

from utils.config import get_settings

settings = get_settings()

class PinImageGenerator:
    def __init__(self, width: int = 1000, height: int = 1500):
        self.pin_width = width or settings.PIN_WIDTH
        self.pin_height = height or settings.PIN_HEIGHT
    
    async def download_image(self, url: str) -> Optional[Image.Image]:
        """Download an image from a URL."""
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(url)
                response.raise_for_status()
                img = Image.open(BytesIO(response.content))
                return img
        except Exception:
            return None
    
    def create_pin_layout(
        self,
        product_image: Image.Image,
        title: str,
        price: Optional[str] = None,
        discount: Optional[str] = None,
        rating: Optional[float] = None
    ) -> Image.Image:
        """Create a Pinterest pin layout with product image and overlay text."""
        # Create canvas
        canvas = Image.new("RGB", (self.pin_width, self.pin_height), "white")
        draw = ImageDraw.Draw(canvas)
        
        # Resize and paste product image
        img_width = self.pin_width - 40
        img_height = int(img_width * 1.2)
        product_image = product_image.resize((img_width, img_height), Image.LANCZOS)
        canvas.paste(product_image, (20, 20))
        
        # Add title text
        text_y = img_height + 40
        max_chars = 60
        if len(title) > max_chars:
            title = title[:max_chars] + "..."
        
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
            font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 28)
        except OSError:
            font = ImageFont.load_default()
            font_small = ImageFont.load_default()
        
        draw.text((40, text_y), title, fill="black", font=font)
        
        # Add price if available
        if price:
            price_text = f"${price}"
            draw.text((40, text_y + 50), price_text, fill="#B12704", font=font)
        
        # Add rating if available
        if rating:
            rating_text = f"★ {rating:.1f}"
            draw.text((40, text_y + 100), rating_text, fill="#FFA41C", font=font_small)
        
        return canvas
    
    async def generate_pin_image(self, product_image_url: str, title: str, price: Optional[float] = None, discount: Optional[float] = None, rating: Optional[float] = None) -> Optional[BytesIO]:
        """Full pipeline: download product image and create pin layout."""
        product_image = await self.download_image(product_image_url)
        if product_image is None:
            return None
        
        price_str = f"${price:.2f}" if price else None
        discount_str = f"{discount:.0f}% OFF" if discount else None
        
        pin_image = self.create_pin_layout(
            product_image=product_image,
            title=title,
            price=price_str,
            discount=discount_str,
            rating=rating
        )
        
        buf = BytesIO()
        pin_image.save(buf, format="PNG")
        buf.seek(0)
        return buf