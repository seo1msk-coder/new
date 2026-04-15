"""
Клавиатуры и кнопки бота
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


# ==================== ГЛАВНОЕ МЕНЮ ====================

def main_menu_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🃏 Расклад Таро", callback_data="menu_tarot"),
        InlineKeyboardButton(text="⭐ Гороскоп", callback_data="menu_horoscope"),
    )
    builder.row(
        InlineKeyboardButton(text="💕 Совместимость", callback_data="menu_compatibility"),
    )
    builder.row(
        InlineKeyboardButton(text="👑 Подписка", callback_data="menu_subscribe"),
        InlineKeyboardButton(text="👤 Мой профиль", callback_data="menu_profile"),
    )
    return builder.as_markup()


# ==================== ТАРО ====================

def tarot_types_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="💕 На любовь", callback_data="tarot_love"),
        InlineKeyboardButton(text="💼 На карьеру", callback_data="tarot_career"),
    )
    builder.row(
        InlineKeyboardButton(text="🌟 На день", callback_data="tarot_day"),
        InlineKeyboardButton(text="🎯 На ситуацию", callback_data="tarot_general"),
    )
    builder.row(
        InlineKeyboardButton(text="🔯 Кельтский крест (10 карт)", callback_data="tarot_celtic"),
    )
    builder.row(
        InlineKeyboardButton(text="◀️ Назад", callback_data="back_main"),
    )
    return builder.as_markup()


def skip_question_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✨ Без вопроса (общий расклад)", callback_data="skip_question"),
        InlineKeyboardButton(text="❌ Отмена", callback_data="back_main"),
    )
    return builder.as_markup()


# ==================== ГОРОСКОП ====================

ZODIAC_SIGNS = [
    ("♈ Овен", "aries"), ("♉ Телец", "taurus"), ("♊ Близнецы", "gemini"),
    ("♋ Рак", "cancer"), ("♌ Лев", "leo"), ("♍ Дева", "virgo"),
    ("♎ Весы", "libra"), ("♏ Скорпион", "scorpio"), ("♐ Стрелец", "sagittarius"),
    ("♑ Козерог", "capricorn"), ("♒ Водолей", "aquarius"), ("♓ Рыбы", "pisces"),
]

ZODIAC_RU = {
    "aries": "Овен", "taurus": "Телец", "gemini": "Близнецы",
    "cancer": "Рак", "leo": "Лев", "virgo": "Дева",
    "libra": "Весы", "scorpio": "Скорпион", "sagittarius": "Стрелец",
    "capricorn": "Козерог", "aquarius": "Водолей", "pisces": "Рыбы",
}


def zodiac_kb(callback_prefix: str = "zodiac") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for i in range(0, len(ZODIAC_SIGNS), 3):
        row = ZODIAC_SIGNS[i:i+3]
        builder.row(*[
            InlineKeyboardButton(text=name, callback_data=f"{callback_prefix}_{key}")
            for name, key in row
        ])
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="back_main"))
    return builder.as_markup()


def horoscope_period_kb(zodiac: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📅 На сегодня", callback_data=f"horo_today_{zodiac}"),
        InlineKeyboardButton(text="📆 На неделю", callback_data=f"horo_week_{zodiac}"),
    )
    builder.row(
        InlineKeyboardButton(text="🗓 На месяц", callback_data=f"horo_month_{zodiac}"),
    )
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="menu_horoscope"))
    return builder.as_markup()


# ==================== СОВМЕСТИМОСТЬ ====================

def compatibility_zodiac_kb(step: int, first_sign: str = None) -> InlineKeyboardMarkup:
    prefix = f"compat2_{first_sign}" if step == 2 else "compat1"
    return zodiac_kb(callback_prefix=prefix)


# ==================== ПОДПИСКА / ОПЛАТА ====================

def subscription_kb(use_stars: bool = True) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    if use_stars:
        builder.row(
            InlineKeyboardButton(text="✨ 1 расклад — 75 ⭐", callback_data="buy_stars_single"),
        )
        builder.row(
            InlineKeyboardButton(text="📦 Базовая — 200 ⭐/мес (5 раскладов)", callback_data="buy_stars_base"),
        )
        builder.row(
            InlineKeyboardButton(text="👑 Премиум — 400 ⭐/мес (безлимит)", callback_data="buy_stars_premium"),
        )
    else:
        builder.row(
            InlineKeyboardButton(text="✨ 1 расклад — 149₽", callback_data="buy_rub_single"),
        )
        builder.row(
            InlineKeyboardButton(text="📦 Базовая — 399₽/мес", callback_data="buy_rub_base"),
        )
        builder.row(
            InlineKeyboardButton(text="👑 Премиум — 799₽/мес", callback_data="buy_rub_premium"),
        )
    
    builder.row(
        InlineKeyboardButton(text="🎁 Получить бесплатно (пригласить друга)", callback_data="referral_info"),
    )
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="back_main"))
    return builder.as_markup()


def after_reading_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔮 Ещё расклад", callback_data="menu_tarot"),
        InlineKeyboardButton(text="👑 Подписка", callback_data="menu_subscribe"),
    )
    builder.row(InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_main"))
    return builder.as_markup()


def paywall_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="👑 Купить подписку", callback_data="menu_subscribe"),
    )
    builder.row(
        InlineKeyboardButton(text="🎁 Пригласить друга (бесплатный расклад)", callback_data="referral_info"),
    )
    builder.row(InlineKeyboardButton(text="◀️ Главное меню", callback_data="back_main"))
    return builder.as_markup()
