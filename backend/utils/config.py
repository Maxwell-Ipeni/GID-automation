"""
Configuration settings for the Get It Done application.
Supports environment variables and .env files.
"""

import os
from pydantic_settings import BaseSettings
from functools import lru_cache

AMAZON_REGIONS: dict = {
    "us": {"domain": "com", "base_url": "https://www.amazon.com"},
    "uk": {"domain": "co.uk", "base_url": "https://www.amazon.co.uk"},
    "de": {"domain": "de", "base_url": "https://www.amazon.de"},
    "fr": {"domain": "fr", "base_url": "https://www.amazon.fr"},
    "it": {"domain": "it", "base_url": "https://www.amazon.it"},
    "es": {"domain": "es", "base_url": "https://www.amazon.es"},
}

PINTEREST_REGIONS = ["US", "GB", "DE", "FR", "IT", "ES"]

AMAZON_PINTEREST_MAP = {
    "US": "us",
    "GB": "uk",
    "DE": "de",
    "FR": "fr",
    "IT": "it",
    "ES": "es",
}


def domain_for_region(region: str) -> str:
    info = AMAZON_REGIONS.get(region)
    return info["domain"] if info else "com"


def base_url_for_region(region: str) -> str:
    info = AMAZON_REGIONS.get(region)
    return info["base_url"] if info else "https://www.amazon.com"


class Settings(BaseSettings):
    APP_NAME: str = "Get It Done"
    DEBUG: bool = False

    AMAZON_AFFILIATE_TAG: str
    AMAZON_BASE_URL: str = "https://www.amazon.com"

    PINTEREST_APP_ID: str = ""
    PINTEREST_APP_SECRET: str = ""
    PINTEREST_ACCESS_TOKEN: str = ""
    PINTEREST_BOARD_ID: str = ""
    PINTEREST_API_BASE: str = "https://api.pinterest.com/v5"

    PUBLISH_DELAY_MIN_MINUTES: int = 60
    PUBLISH_DELAY_MAX_MINUTES: int = 180
    PUBLISH_RETRY_ATTEMPTS: int = 1
    PUBLISH_RETRY_DELAY_SECONDS: int = 5

    SCRAPE_DELAY_MIN: int = 5
    SCRAPE_DELAY_MAX: int = 10
    USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

    SCRAPE_INTERVAL_HOURS: int = 12
    PUBLISH_INTERVAL_MINUTES: int = 360

    BUFFER_API_KEY: str = ""
    BUFFER_PINTEREST_CHANNEL_ID: str = ""
    BUFFER_TWITTER_CHANNEL_ID: str = ""
    TWITTER_MAX_CHARS: int = 280

    PIN_WIDTH: int = 1000
    PIN_HEIGHT: int = 1500
    PIN_IMAGE_DIR: str = "generated_images"

    NVIDIA_API_KEY: str = ""
    NVIDIA_API_BASE: str = "https://integrate.api.nvidia.com/v1"
    NVIDIA_MODEL: str = "meta/llama-3.3-70b-instruct"
    NVIDIA_VISION_MODEL: str = "meta/llama-3.2-11b-vision-instruct"
    NVIDIA_FALLBACK_MODEL: str = "meta/llama-3.1-8b-instruct"

    CONVEX_URL: str

    # Security settings
    API_KEY: str = ""
    ALLOWED_ORIGINS: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

@lru_cache()
def get_settings() -> Settings:
    return Settings()
