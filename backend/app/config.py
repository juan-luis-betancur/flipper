import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    supabase_url: str
    supabase_service_role_key: str
    supabase_jwt_secret: str
    cron_secret: str
    telegram_webhook_secret: str
    scrape_delay_seconds: float
    scrape_max_properties: int
    user_agent: str


@lru_cache
def get_settings() -> Settings:
    return Settings(
        supabase_url=os.getenv("SUPABASE_URL", ""),
        supabase_service_role_key=os.getenv("SUPABASE_SERVICE_ROLE_KEY", ""),
        supabase_jwt_secret=os.getenv("SUPABASE_JWT_SECRET", ""),
        cron_secret=os.getenv("CRON_SECRET", ""),
        telegram_webhook_secret=os.getenv("TELEGRAM_WEBHOOK_SECRET", "change-me"),
        scrape_delay_seconds=float(os.getenv("SCRAPE_DELAY_SECONDS", "3.5")),
        scrape_max_properties=int(os.getenv("SCRAPE_MAX_PROPERTIES", "100")),
        user_agent=os.getenv(
            "SCRAPE_USER_AGENT",
            "FlipperMVP/1.0 (+https://example.com)",
        ),
    )
