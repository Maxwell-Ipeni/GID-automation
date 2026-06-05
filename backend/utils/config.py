"""
Configuration settings for the Get It Done application.
Supports environment variables and .env files.
"""

import os
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Get It Done"
    DEBUG: bool = False
    
    # Amazon Affiliate
    AMAZON_AFFILIATE_TAG: str = "maxwel06-20"
    AMAZON_BASE_URL: str = "https://www.amazon.com"
    
    # Pinterest API
    PINTEREST_APP_ID: str = ""
    PINTEREST_APP_SECRET: str = ""
    PINTEREST_ACCESS_TOKEN: str = ""
    PINTEREST_BOARD_ID: str = ""
    PINTEREST_API_BASE: str = "https://api.pinterest.com/v5"
    
    # Publishing
    PUBLISH_DELAY_MIN_MINUTES: int = 60
    PUBLISH_DELAY_MAX_MINUTES: int = 180
    PUBLISH_RETRY_ATTEMPTS: int = 1
    PUBLISH_RETRY_DELAY_SECONDS: int = 5
    
    # Scraping
    SCRAPE_DELAY_MIN: int = 5
    SCRAPE_DELAY_MAX: int = 10
    USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    
    # Scheduler
    SCRAPE_INTERVAL_HOURS: int = 12
    PUBLISH_INTERVAL_MINUTES: int = 360
    
    # Buffer (fallback publisher)
    BUFFER_API_KEY: str = ""
    BUFFER_PINTEREST_CHANNEL_ID: str = ""
    BUFFER_TWITTER_CHANNEL_ID: str = ""
    TWITTER_MAX_CHARS: int = 280

    # Image generation
    PIN_WIDTH: int = 1000
    PIN_HEIGHT: int = 1500
    PIN_IMAGE_DIR: str = "generated_images"
    
    # NVIDIA AI (content generation)
    NVIDIA_API_KEY: str = ""
    NVIDIA_API_BASE: str = "https://integrate.api.nvidia.com/v1"
    NVIDIA_MODEL: str = "meta/llama-3.3-70b-instruct"
    NVIDIA_VISION_MODEL: str = "meta/llama-3.2-11b-vision-instruct"
    NVIDIA_FALLBACK_MODEL: str = "meta/llama-3.1-8b-instruct"
    
    # Convex DB
    CONVEX_URL: str = ""
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

@lru_cache()
def get_settings() -> Settings:
    return Settings()
