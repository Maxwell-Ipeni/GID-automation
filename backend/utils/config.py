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
    AMAZON_AFFILIATE_TAG: str = "yourtag-20"
    AMAZON_BASE_URL: str = "https://www.amazon.com"
    
    # Pinterest API
    PINTEREST_ACCESS_TOKEN: str = "your_pinterest_token"
    PINTEREST_BOARD_ID: str = "your_board_id"
    PINTEREST_API_BASE: str = "https://api.pinterest.com/v5"
    
    # Scraping
    SCRAPE_DELAY_MIN: int = 2
    SCRAPE_DELAY_MAX: int = 5
    USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    
    # Scheduler
    SCRAPE_INTERVAL_HOURS: int = 4
    PUBLISH_INTERVAL_MINUTES: int = 30
    
    # Image generation
    PIN_WIDTH: int = 1000
    PIN_HEIGHT: int = 1500
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

@lru_cache()
def get_settings() -> Settings:
    return Settings()
