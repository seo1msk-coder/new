"""
Конфигурация бота
"""
import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Config:
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN")
    ADMIN_IDS: list = None
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///astro_bot.db")
    YOOKASSA_SHOP_ID: str = os.getenv("YOOKASSA_SHOP_ID", "")
    YOOKASSA_SECRET_KEY: str = os.getenv("YOOKASSA_SECRET_KEY", "")
    USE_TELEGRAM_STARS: bool = os.getenv("USE_TELEGRAM_STARS", "true").lower() == "true"
    PRICE_SINGLE_SPREAD: int = 149
    PRICE_MONTHLY_BASE: int = 399
    PRICE_MONTHLY_PREMIUM: int = 799
    STARS_SINGLE_SPREAD: int = 75
    STARS_MONTHLY_BASE: int = 200
    STARS_MONTHLY_PREMIUM: int = 400
    FREE_SPREADS_TOTAL: int = 1
    BASE_SPREADS_PER_MONTH: int = 5

    def __post_init__(self):
        if self.ADMIN_IDS is None:
            admin_str = os.getenv("ADMIN_IDS", "")
            self.ADMIN_IDS = [int(x) for x in admin_str.split(",") if x.strip().isdigit()]

config = Config()
