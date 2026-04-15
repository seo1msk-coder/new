"""
Хендлер /start и главного меню
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command

from services.database import get_or_create_user, update_user
from keyboards.kb import main_menu_kb

router = Router()

WELCOME_TEXT = """🔮 *Добро пожаловать, дорогой человек...*

Я — Алина, ваш личный астролог и проводник в мир звёзд 🌙

Я чувствую энергии, читаю карты Таро и вижу то, что скрыто от глаз. Каждый расклад — это послание Вселенной *лично для вас.*

Что я могу сделать для вас:
✦ 🃏 *Расклады Таро* — на любовь, карьеру, ситуацию
✦ ⭐ *Персональный гороскоп* — на день, неделю, месяц  
✦ 💕 *Совместимость пар* — узнайте вашу связь
✦ 🌙 *Кельтский крест* — глубокий анализ жизни

*Первый расклад — бесплатно.* Звёзды уже ждут вас...

👇 Выберите, с чего начнём:"""

MAIN_MENU_TEXT = """🔮 *Главное меню*

Звёзды слышат вас. Что хотите узнать сегодня?"""


@router.message(CommandStart())
async def cmd_start(message: Message):
    # Обрабатываем реферальный код
    args = message.text.split()
    referrer_id = None
    if len(args) > 1:
        try:
            referrer_id = int(args[1].replace("ref", ""))
        except:
            pass

    user = await get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )

    if referrer_id and referrer_id != message.from_user.id:
        await update_user(message.from_user.id, referred_by=referrer_id)
        # TODO: начислить бонус рефереру

    await message.answer(
        WELCOME_TEXT,
        parse_mode="Markdown",
        reply_markup=main_menu_kb()
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    text = """🔮 *Помощь — ИИ Астролог*

*Как пользоваться:*
1. Выберите тип расклада из меню
2. Задайте вопрос (или пропустите для общего расклада)
3. Получите персональный ответ от Алины ✨

*Тарифы:*
• Бесплатно: 1 расклад для новых пользователей
• Базовая (200 ⭐/мес): 5 раскладов в месяц
• Премиум (400 ⭐/мес): безлимитные расклады

*Контакт:* @support\_astro\_bot
*Возникли проблемы?* Напишите нам!"""
    await message.answer(text, parse_mode="Markdown")


@router.callback_query(F.data == "back_main")
async def back_to_main(callback: CallbackQuery):
    await callback.message.edit_text(
        MAIN_MENU_TEXT,
        parse_mode="Markdown",
        reply_markup=main_menu_kb()
    )


@router.callback_query(F.data == "menu_profile")
async def show_profile(callback: CallbackQuery):
    from services.database import AsyncSessionLocal, User
    from sqlalchemy import select

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        user = result.scalar_one_or_none()

    if not user:
        await callback.answer("Профиль не найден")
        return

    from datetime import datetime
    sub_status = {
        "free": "🆓 Бесплатный",
        "base": "📦 Базовая",
        "premium": "👑 Премиум",
    }.get(user.subscription_type, "🆓 Бесплатный")

    expires = ""
    if user.subscription_expires and user.subscription_expires > datetime.utcnow():
        expires = f"\n📅 Активна до: {user.subscription_expires.strftime('%d.%m.%Y')}"

    zodiac = f"\n♈ Знак: {user.zodiac_sign}" if user.zodiac_sign else ""
    birth = f"\n🎂 Дата рождения: {user.birth_date}" if user.birth_date else ""

    text = f"""👤 *Ваш профиль*

🔮 Имя: {user.first_name or 'не указано'}
{zodiac}{birth}

📊 *Подписка:* {sub_status}{expires}
📈 Раскладов использовано: {user.total_spreads_free}
👥 Приглашено друзей: {user.referral_count}

_Используйте /start для главного меню_"""

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="👑 Улучшить подписку", callback_data="menu_subscribe"),
        InlineKeyboardButton(text="◀️ Назад", callback_data="back_main"),
    )

    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=builder.as_markup())
