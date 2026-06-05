import asyncio
import logging
import os
import re
from pathlib import Path
from typing import Dict, Optional

import httpx

logger = logging.getLogger(__name__)

FONTS_DIR = Path(__file__).resolve().parent.parent / "fonts"

FONT_REGISTRY: Dict[str, Dict] = {
    "Poppins": {
        "dir": "poppins",
        "weights": {
            400: "Poppins-Regular.ttf",
            600: "Poppins-SemiBold.ttf",
            700: "Poppins-Bold.ttf",
        },
    },
    "Lato": {
        "dir": "lato",
        "weights": {
            400: "Lato-Regular.ttf",
            700: "Lato-Bold.ttf",
            900: "Lato-Black.ttf",
        },
    },
    "Mukta": {
        "dir": "mukta",
        "weights": {
            400: "Mukta-Regular.ttf",
            600: "Mukta-SemiBold.ttf",
            700: "Mukta-Bold.ttf",
            800: "Mukta-ExtraBold.ttf",
        },
    },
    "Bebas Neue": {
        "dir": "bebasneue",
        "weights": {
            400: "BebasNeue-Regular.ttf",
        },
    },
    "Pacifico": {
        "dir": "pacifico",
        "weights": {
            400: "Pacifico-Regular.ttf",
        },
    },
}

GITHUB_RAW = "https://github.com/google/fonts/raw/main/ofl"


class FontManager:
    def __init__(self):
        self._paths: Dict[str, Dict[int, str]] = {}
        self._initialized = False

    def _font_path(self, family: str, weight: int) -> Path:
        entry = FONT_REGISTRY[family]
        return FONTS_DIR / entry["dir"] / entry["weights"][weight]

    def ensure_fonts(self) -> None:
        for family, entry in FONT_REGISTRY.items():
            for weight in entry["weights"]:
                path = self._font_path(family, weight)
                if not path.exists():
                    logger.warning(f"Font not found: {path} — will try downloading on demand")

    async def download_font(self, family: str, weight: int) -> Optional[str]:
        entry = FONT_REGISTRY.get(family)
        if not entry:
            logger.error(f"Unknown font family: {family}")
            return None
        filename = entry["weights"].get(weight)
        if not filename:
            logger.error(f"Weight {weight} not available for {family}")
            return None

        dest = self._font_path(family, weight)
        if dest.exists():
            return str(dest)

        dest.parent.mkdir(parents=True, exist_ok=True)

        candidates = [
            f"{GITHUB_RAW}/{entry['dir']}/{filename}",
            f"{GITHUB_RAW}/{entry['dir']}/static/{filename}",
        ]
        for url in candidates:
            try:
                async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
                    resp = await client.get(url)
                    resp.raise_for_status()
                    dest.write_bytes(resp.content)
                logger.info(f"Downloaded font: {family} {weight} → {dest}")
                return str(dest)
            except Exception:
                continue

        logger.error(f"Failed to download {family} {weight} from any URL")
        return None

    async def get_font(self, family: str, weight: int = 400) -> Optional[str]:
        path = self._font_path(family, weight)
        if path.exists():
            return str(path)
        return await self.download_font(family, weight)

    async def get_fonts_for_template(self, headline_family: str, body_family: str, headline_weight: int = 700, body_weight: int = 400) -> Dict[str, str]:
        headline = await self.get_font(headline_family, headline_weight)
        body = await self.get_font(body_family, body_weight)
        bold_body = await self.get_font(body_family, 700) if body_family != headline_family else headline
        return {
            "headline": headline or "",
            "body": body or "",
            "bold_body": bold_body or "",
        }


font_manager = FontManager()
