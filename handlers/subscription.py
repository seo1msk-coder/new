"""
Хендлер подписки и тарифов
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery

from keyboards.kb import subscription_kb
from config import config

router = Router()

SUBSCRIPTION_TEXT = """👑 *Тарифы Алины*

Откройте доступ к полной силе звёзд ✨

━━━━━━━━━━━━━━━━━━━━━━
✨ *Разовый расклад* — 75 ⭐
• Один расклад на выбор
• Изображение карт
• Полный текст от Алины

━━━━━━━━━━━━━━━━━━━━━━
📦 *Базовая* — 200 ⭐/месяц
• 5 раскладов в месяц
• Все типы раскладов
• Персональный гороскоп
• Анализ совместимости

━━━━━━━━━━━━━━━━━━━━━━
👑 *Премиум* — 400 ⭐/месяц
• ∞ Безлимитные расклады
• Кельтский крест (10 карт)
• Приоритетная генерация
• Расширенные прогнозы

━━━━━━━━━━━━━━━━━━━━━━
🎁 *Бесплатно:* Пригласите друга
и получите 1 расклад в подарок!

_Telegram Stars — безопасная оплата прямо в Telegram_"""

REFERRAL_TEXT = """🎁 *Реферальная программа*

Пригласите друга — получите бесплатный расклад!

*Ваша реферальная ссылка:*
`https://t.me/YourBotName?start=ref{user_id}`

*Как это работает:*
1. Поделитесь ссылкой с другом
2. Друг регистрируется и делает 1й расклад
3. Вы получаете 1 бесплатный расклад 🎉

*Ваш счёт:* {referral_count} приглашённых друзей"""


@router.callback_query(F.data == "menu_subscribe")
async def show_subscription(callback: CallbackQuery):
    await callback.message.edit_text(
        SUBSCRIPTION_TEXT,
        parse_mode="Markdown",
        reply_markup=subscription_kb(use_stars=config.USE_TELEGRAM_STARS)
    )


@router.callback_query(F.data == "referral_info")
async def show_referral(callback: CallbackQuery):
    from services.database import AsyncSessionLocal, User
    from sqlalchemy import select
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        user = result.scalar_one_or_none()

    ref_count = user.referral_count if user else 0
    
    text = REFERRAL_TEXT.format(
        user_id=callback.from_user.id,
        referral_count=ref_count
    )

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="◀️ К тарифам", callback_data="menu_subscribe"))
    
    await callback.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=builder.as_markup()
    )
