from dataclasses import dataclass
from typing import Dict, Optional, Tuple


@dataclass
class PinTemplate:
    name: str
    image_height_ratio: float  # 0.0-1.0, portion of pin taken by product image
    headline_font: str
    headline_weight: int
    body_font: str
    body_weight: int
    headline_size: int
    body_size: int
    cta_style: str
    accent_style: str
    colors: Dict[str, Tuple[int, int, int]]
    background_treatment: str
    image_style: str
    text_align: str = "left"
    headline_color: Tuple[int, int, int] = (69, 61, 53)
    body_color: Tuple[int, int, int] = (69, 61, 53)
    text_bg_color: Tuple[int, int, int] = (245, 240, 235)
    badge_color: Tuple[int, int, int] = (240, 208, 208)
    image_ratio: float = 1.0


@dataclass
class CategoryMapping:
    template_name: str
    board_name: str


PIN_WIDTH = 1000
PIN_HEIGHT = 1500

CATEGORY_TEMPLATES: Dict[str, CategoryMapping] = {
    "fashion": CategoryMapping("elegant", "Fashion Picks"),
    "beauty": CategoryMapping("elegant", "Beauty Faves"),
    "home": CategoryMapping("warm", "Home Finds"),
    "kitchen": CategoryMapping("warm", "Kitchen Essentials"),
    "food": CategoryMapping("warm", "Foodie Finds"),
    "baby": CategoryMapping("warm", "Baby Must-Haves"),
    "electronics": CategoryMapping("minimal", "Tech Gadgets"),
    "tech": CategoryMapping("minimal", "Tech Gadgets"),
    "office": CategoryMapping("minimal", "Office Upgrades"),
    "sports": CategoryMapping("bold", "Sports & Outdoors"),
    "outdoors": CategoryMapping("bold", "Sports & Outdoors"),
    "automotive": CategoryMapping("bold", "Auto & Tools"),
    "tools": CategoryMapping("bold", "Tools & Workshop"),
    "pet": CategoryMapping("warm", "Pet Loves"),
    "toys": CategoryMapping("fun", "Toy Box"),
    "books": CategoryMapping("elegant", "Book Nook"),
    "music": CategoryMapping("elegant", "Sounds & Vibes"),
    "default": CategoryMapping("warm", "Finds & Faves"),
}

DARK_BROWN = (69, 61, 53)
WHITE = (255, 255, 255)
WARM_BEIGE_TOP = (245, 240, 235)
WARM_BEIGE_BOTTOM = (231, 221, 212)
WARM_TAUPE = (176, 151, 131)
PINK_BADGE = (240, 208, 208)
AMAZON_ORANGE = (255, 153, 0)
LIGHT_GRAY = (245, 245, 245)
MID_GRAY = (200, 200, 200)
DARK_BG = (14, 12, 13)
BRICK_RED = (155, 73, 58)
DEEP_RED = (154, 28, 27)
SOFT_ROSE = (230, 200, 195)
WARM_GOLD = (200, 170, 110)

TEMPLATES: Dict[str, PinTemplate] = {
    "warm": PinTemplate(
        name="warm",
        image_height_ratio=0.82,
        headline_font="Mukta",
        headline_weight=700,
        body_font="Poppins",
        body_weight=400,
        headline_size=38,
        body_size=22,
        cta_style="pill",
        accent_style="badge",
        colors={
            "bg_top": WARM_BEIGE_TOP,
            "bg_bottom": WARM_BEIGE_BOTTOM,
            "accent": WARM_TAUPE,
            "badge": PINK_BADGE,
            "cta": WARM_TAUPE,
            "cta_text": WHITE,
        },
        background_treatment="gradient",
        image_style="full_bleed",
        text_align="left",
        headline_color=DARK_BROWN,
        body_color=DARK_BROWN,
        text_bg_color=WARM_BEIGE_TOP,
        badge_color=PINK_BADGE,
    ),
    "elegant": PinTemplate(
        name="elegant",
        image_height_ratio=0.80,
        headline_font="Lato",
        headline_weight=900,
        body_font="Lato",
        body_weight=400,
        headline_size=36,
        body_size=22,
        cta_style="underline",
        accent_style="badge",
        colors={
            "bg_top": (240, 232, 224),
            "bg_bottom": (225, 215, 205),
            "accent": SOFT_ROSE,
            "badge": SOFT_ROSE,
            "cta": (180, 140, 120),
            "cta_text": WHITE,
        },
        background_treatment="gradient",
        image_style="full_bleed",
        text_align="left",
        headline_color=DARK_BROWN,
        body_color=DARK_BROWN,
        text_bg_color=(240, 232, 224),
        badge_color=SOFT_ROSE,
    ),
    "minimal": PinTemplate(
        name="minimal",
        image_height_ratio=0.78,
        headline_font="Poppins",
        headline_weight=700,
        body_font="Poppins",
        body_weight=400,
        headline_size=34,
        body_size=20,
        cta_style="outline",
        accent_style="line",
        colors={
            "bg_top": LIGHT_GRAY,
            "bg_bottom": (235, 235, 240),
            "accent": (33, 150, 243),
            "badge": (33, 150, 243),
            "cta": (33, 150, 243),
            "cta_text": WHITE,
        },
        background_treatment="solid",
        image_style="full_bleed",
        text_align="left",
        headline_color=(50, 50, 60),
        body_color=(100, 100, 110),
        text_bg_color=LIGHT_GRAY,
        badge_color=(200, 220, 240),
    ),
    "bold": PinTemplate(
        name="bold",
        image_height_ratio=0.85,
        headline_font="Mukta",
        headline_weight=800,
        body_font="Poppins",
        body_weight=600,
        headline_size=42,
        body_size=24,
        cta_style="solid",
        accent_style="badge",
        colors={
            "bg_top": DARK_BG,
            "bg_bottom": (10, 8, 9),
            "accent": BRICK_RED,
            "badge": DEEP_RED,
            "cta": BRICK_RED,
            "cta_text": WHITE,
        },
        background_treatment="gradient",
        image_style="full_bleed",
        text_align="left",
        headline_color=WHITE,
        body_color=(200, 195, 190),
        text_bg_color=(20, 18, 19),
        badge_color=DEEP_RED,
    ),
    "fun": PinTemplate(
        name="fun",
        image_height_ratio=0.82,
        headline_font="Poppins",
        headline_weight=700,
        body_font="Poppins",
        body_weight=400,
        headline_size=38,
        body_size=22,
        cta_style="pill",
        accent_style="badge",
        colors={
            "bg_top": (80, 40, 80),
            "bg_bottom": (50, 25, 60),
            "accent": (255, 200, 50),
            "badge": (255, 200, 50),
            "cta": (255, 200, 50),
            "cta_text": (50, 25, 60),
        },
        background_treatment="gradient",
        image_style="full_bleed",
        text_align="left",
        headline_color=WHITE,
        body_color=(220, 210, 220),
        text_bg_color=(60, 30, 60),
        badge_color=(255, 200, 50),
    ),
}


def get_template_for_category(category: Optional[str]) -> PinTemplate:
    if not category:
        return TEMPLATES["warm"]
    for key, mapping in CATEGORY_TEMPLATES.items():
        if key in category.lower():
            return TEMPLATES[mapping.template_name]
    return TEMPLATES["warm"]


def get_board_name_for_category(category: Optional[str]) -> str:
    if not category:
        return CATEGORY_TEMPLATES["default"].board_name
    for key, mapping in CATEGORY_TEMPLATES.items():
        if key in category.lower():
            return mapping.board_name
    return CATEGORY_TEMPLATES["default"].board_name


def get_all_board_names() -> set:
    return {m.board_name for m in CATEGORY_TEMPLATES.values()}
