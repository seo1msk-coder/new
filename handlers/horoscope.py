"""
Хендлер гороскопов
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram import Bot

from services.ai_service import generate_horoscope
from services.database import can_use_spread, increment_spread_count, AsyncSessionLocal, User
from keyboards.kb import zodiac_kb, horoscope_period_kb, after_reading_kb, paywall_kb, ZODIAC_RU
from sqlalchemy import select

router = Router()

PAYWALL_TEXT = """🌙 *Гороскоп требует подписки*

Первый бесплатный расклад уже использован...

*Получите доступ к персональным гороскопам:*
📦 Базовая (200 ⭐/мес) — 5 раскладов
👑 Премиум (400 ⭐/мес) — безлимит

_Звёзды ждут вас..._"""


@router.callback_query(F.data == "menu_horoscope")
async def show_horoscope_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "⭐ *Персональный гороскоп*\n\n"
        "Выберите ваш знак зодиака:\n\n"
        "_Звёзды знают всё о вашей судьбе..._",
        parse_mode="Markdown",
        reply_markup=zodiac_kb("horo_sign")
    )


@router.callback_query(F.data.startswith("horo_sign_"))
async def zodiac_selected(callback: CallbackQuery):
    zodiac = callback.data.replace("horo_sign_", "")
    zodiac_name = ZODIAC_RU.get(zodiac, zodiac)

    await callback.message.edit_text(
        f"⭐ *{zodiac_name}*\n\n"
        f"На какой период составить гороскоп?",
        parse_mode="Markdown",
        reply_markup=horoscope_period_kb(zodiac)
    )


@router.callback_query(F.data.startswith("horo_today_") | F.data.startswith("horo_week_") | F.data.startswith("horo_month_"))
async def period_selected(callback: CallbackQuery):
    parts = callback.data.split("_")
    period = parts[1]   # today / week / month
    zodiac = parts[2]   # sign key

    # Проверяем доступ
    can_use, reason = await can_use_spread(callback.from_user.id)
    if not can_use:
        await callback.message.edit_text(
            PAYWALL_TEXT,
            parse_mode="Markdown",
            reply_markup=paywall_kb()
        )
        return

    zodiac_name = ZODIAC_RU.get(zodiac, zodiac)
    periods_text = {"today": "сегодня", "week": "неделю", "month": "месяц"}
    period_str = periods_text.get(period, "сегодня")

    loading_msg = await callback.message.edit_text(
        f"⭐ *Алина составляет гороскоп...*\n\n"
        f"Знак: {zodiac_name} | Период: {period_str}\n\n"
        f"🌙 Звёзды выстраиваются в нужном порядке...\n"
        f"✨ Ваше послание готовится...",
        parse_mode="Markdown"
    )

    # Получаем дату рождения пользователя
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        user = result.scalar_one_or_none()

    birth_date = str(user.birth_date) if user and user.birth_date else None

    try:
        horoscope_text = await generate_horoscope(zodiac_name, period, birth_date)

        from config import config
        bot = Bot(token=config.BOT_TOKEN)

        try:
            await loading_msg.delete()
        except:
            pass

        header = f"⭐ *Гороскоп {zodiac_name} на {period_str}*\n\n"
        full_text = header + horoscope_text

        chunks = [full_text[i:i+4000] for i in range(0, len(full_text), 4000)]
        for i, chunk in enumerate(chunks):
            kb = after_reading_kb() if i == len(chunks) - 1 else None
            await bot.send_message(
                chat_id=callback.message.chat.id,
                text=chunk,
                parse_mode="Markdown",
                reply_markup=kb
            )

        await increment_spread_count(
            callback.from_user.id,
            f"horoscope_{period}",
            f"{zodiac_name} {period_str}",
            horoscope_text
        )

        await bot.session.close()

    except Exception as e:
        await loading_msg.edit_text(
            f"😔 Произошла ошибка: {str(e)[:100]}\n\nПопробуйте через минуту.",
            reply_markup=after_reading_kb()
        )
