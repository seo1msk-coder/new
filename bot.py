#!/usr/bin/env python3
import asyncio, logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand
from config import config
from handlers.start import router as start_router
from handlers.tarot import router as tarot_router
from handlers.horoscope import router as horoscope_router
from handlers.compatibility import router as compat_router
from handlers.subscription import router as sub_router
from handlers.payment import router as payment_router
from services.database import init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def set_commands(bot):
    await bot.set_my_commands([
        BotCommand(command="start", description="🔮 Начать"),
        BotCommand(command="tarot", description="🃏 Расклад Таро"),
        BotCommand(command="horoscope", description="⭐ Гороскоп"),
        BotCommand(command="compatibility", description="💕 Совместимость"),
        BotCommand(command="subscribe", description="👑 Подписка"),
        BotCommand(command="help", description="❓ Помощь"),
    ])

async def main():
    await init_db()
    bot = Bot(token=config.BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(start_router)
    dp.include_router(tarot_router)
    dp.include_router(horoscope_router)
    dp.include_router(compat_router)
    dp.include_router(sub_router)
    dp.include_router(payment_router)
    await set_commands(bot)
    logger.info("✅ Бот запущен!")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

if __name__ == "__main__":
    asyncio.run(main())
