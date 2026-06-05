import asyncio
import logging
import os
import re
from io import BytesIO
from typing import Optional, Tuple

import httpx
from PIL import Image, ImageDraw, ImageFont

from utils.config import get_settings
from images.font_manager import font_manager, FONTS_DIR
from images.pin_templates import (
    PIN_WIDTH, PIN_HEIGHT, PinTemplate, get_template_for_category,
    get_board_name_for_category, CATEGORY_TEMPLATES,
)

logger = logging.getLogger(__name__)
settings = get_settings()

MARGIN = 40
CONTENT_WIDTH = PIN_WIDTH - 2 * MARGIN
FONT_CACHE: dict = {}


def _load_font(path: str, size: int) -> ImageFont.FreeTypeFont:
    key = (path, size)
    if key not in FONT_CACHE:
        try:
            FONT_CACHE[key] = ImageFont.truetype(path, size)
        except Exception:
            FONT_CACHE[key] = ImageFont.load_default()
    return FONT_CACHE[key]


async def _ensure_fonts(template: PinTemplate) -> dict:
    headline = await font_manager.get_font(template.headline_font, template.headline_weight)
    body = await font_manager.get_font(template.body_font, template.body_weight)
    bold_body = body
    if template.body_font != template.headline_font:
        bold_body = await font_manager.get_font(template.body_font, 700)
    return {"headline": headline, "body": body, "bold_body": bold_body}


def _draw_rounded_rect(draw, rect, radius, fill):
    draw.rounded_rectangle(rect, radius=radius, fill=fill)


def _wrap_text(text: str, font, max_width: int, draw: ImageDraw) -> list:
    words = text.split()
    lines = []
    current = ""
    for word in words:
        test = f"{current} {word}".strip()
        bbox = draw.textbbox((0, 0), test, font=font)
        w = bbox[2] - bbox[0]
        if w <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines if lines else [text]


def _draw_gradient(canvas: Image.Image, color_start: Tuple, color_end: Tuple, y_start=0, y_end=None):
    if y_end is None:
        y_end = canvas.height
    draw = ImageDraw.Draw(canvas)
    height = y_end - y_start
    for y in range(height):
        ratio = y / height
        r = int(color_start[0] * (1 - ratio) + color_end[0] * ratio)
        g = int(color_start[1] * (1 - ratio) + color_end[1] * ratio)
        b = int(color_start[2] * (1 - ratio) + color_end[2] * ratio)
        draw.line([(0, y_start + y), (canvas.width, y_start + y)], fill=(r, g, b))


def _resize_image_cover(img: Image.Image, target_w: int, target_h: int) -> Image.Image:
    img_ratio = img.width / img.height
    target_ratio = target_w / target_h
    if img_ratio > target_ratio:
        new_h = target_h
        new_w = int(target_h * img_ratio)
    else:
        new_w = target_w
        new_h = int(target_w / img_ratio)
    img = img.resize((new_w, new_h), Image.LANCZOS)
    left = (new_w - target_w) // 2
    top = (new_h - target_h) // 2
    return img.crop((left, top, left + target_w, top + target_h))


def _is_dark_bg(color: Tuple[int, int, int]) -> bool:
    return (color[0] + color[1] + color[2]) // 3 < 60


class PinImageGenerator:
    def __init__(self, width: int = PIN_WIDTH, height: int = PIN_HEIGHT):
        self.pin_width = width or settings.PIN_WIDTH
        self.pin_height = height or settings.PIN_HEIGHT
        self.output_dir = settings.PIN_IMAGE_DIR
        os.makedirs(self.output_dir, exist_ok=True)

    async def download_image(self, url: str) -> Optional[Image.Image]:
        try:
            async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
                response = await client.get(url)
                response.raise_for_status()
                img = Image.open(BytesIO(response.content))
                return img.convert("RGB")
        except Exception as e:
            logger.error(f"Failed to download image from {url}: {e}")
            return None

    async def _build_pin(
        self, img: Image.Image, title: str, description: str, hashtags: list,
        template: PinTemplate, fonts: dict
    ) -> Image.Image:
        canvas = Image.new("RGB", (self.pin_width, self.pin_height), "white")
        c = template.colors
        is_dark = _is_dark_bg(c.get("bg_top", template.text_bg_color))

        img_h = int(self.pin_height * template.image_height_ratio)
        product_img = _resize_image_cover(img, self.pin_width, img_h)
        canvas.paste(product_img, (0, 0))

        text_y = img_h
        remaining = self.pin_height - img_h

        # Fill text area background
        if template.background_treatment == "gradient" and "bg_top" in c and "bg_bottom" in c:
            _draw_gradient(canvas, c["bg_top"], c["bg_bottom"], y_start=text_y)
        else:
            draw = ImageDraw.Draw(canvas)
            draw.rectangle([(0, text_y), (self.pin_width, self.pin_height)], fill=template.text_bg_color)

        # Subtle divider line between image and text
        draw = ImageDraw.Draw(canvas)
        accent = c.get("accent", template.text_bg_color)
        draw.line([(MARGIN, text_y), (self.pin_width - MARGIN, text_y)], fill=accent + (100,), width=1)

        text_y += 8
        text_x = MARGIN
        max_text_w = CONTENT_WIDTH
        title_color = template.headline_color
        body_color = template.body_color

        # Title
        head_font = _load_font(fonts["headline"], template.headline_size)
        display_title = title[:90].strip()
        if not display_title:
            display_title = "Check This Out"

        title_lines = _wrap_text(display_title, head_font, max_text_w, draw)
        title_lines = title_lines[:2]

        for line in title_lines:
            draw.text((text_x, text_y), line, fill=title_color, font=head_font)
            text_y += template.headline_size + 4

        text_y += 2

        # Description snippet
        remaining_h = self.pin_height - text_y - 50
        desc_font_size = template.body_size
        desc_font = _load_font(fonts["body"], desc_font_size)
        desc_text = description.strip()
        if not desc_text:
            desc_text = "Click to shop on Amazon"

        desc_lines = _wrap_text(desc_text, desc_font, max_text_w, draw)
        max_desc_lines = max(1, remaining_h // (desc_font_size + 4))
        desc_lines = desc_lines[:max_desc_lines]

        for line in desc_lines:
            draw.text((text_x, text_y), line, fill=body_color, font=desc_font)
            text_y += desc_font_size + 4

        # Amazon Finds badge (bottom-right)
        badge_size = 55
        badge_x = self.pin_width - badge_size - 12
        badge_y = self.pin_height - badge_size - 10
        badge_color = template.badge_color
        _draw_rounded_rect(draw, [(badge_x, badge_y), (badge_x + badge_size, badge_y + badge_size)], 8, badge_color)

        badge_font_size = 9
        try:
            bf = _load_font(fonts["body"], badge_font_size)
        except Exception:
            bf = ImageFont.load_default()

        for i, bword in enumerate(["Amazon", "Finds"]):
            bw = draw.textbbox((0, 0), bword, font=bf)
            bx = badge_x + (badge_size - (bw[2] - bw[0])) // 2
            by = badge_y + 10 + i * 18
            draw.text((bx, by), bword, fill=DARK_BROWN if not is_dark else WHITE, font=bf)

        return canvas

    async def create_pin_layout(
        self,
        product_image: Image.Image,
        title: str,
        description: str = "",
        hashtags: Optional[list] = None,
        category: Optional[str] = None,
    ) -> Image.Image:
        template = get_template_for_category(category)
        fonts = await _ensure_fonts(template)
        return await self._build_pin(product_image, title, description, hashtags or [], template, fonts)

    async def generate_pin_image(
        self,
        product_image_url: str,
        title: str,
        asin: str,
        description: str = "",
        hashtags: Optional[list] = None,
        category: Optional[str] = None,
    ) -> Optional[str]:
        product_image = await self.download_image(product_image_url)
        if product_image is None:
            logger.warning(f"Could not download image for {asin}, using original URL")
            return None

        pin_image = await self.create_pin_layout(
            product_image=product_image,
            title=title,
            description=description,
            hashtags=hashtags,
            category=category,
        )

        filename = f"{asin}.png"
        filepath = os.path.join(self.output_dir, filename)
        pin_image.save(filepath, format="PNG", optimize=True)
        logger.info(f"Generated pin image: {filepath}")

        return filename

    def get_board_name(self, category: Optional[str]) -> str:
        return get_board_name_for_category(category)

    async def generate_pin_image_with_content(
        self,
        product_image_url: str,
        title: str,
        asin: str,
        description: str = "",
        hashtags: Optional[list] = None,
        category: Optional[str] = None,
    ) -> Optional[str]:
        return await self.generate_pin_image(
            product_image_url=product_image_url,
            title=title,
            asin=asin,
            description=description,
            hashtags=hashtags,
            category=category,
        )


WHITE = (255, 255, 255)
DARK_BROWN = (69, 61, 53)
