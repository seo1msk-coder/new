"""
Хендлер платежей — Telegram Stars (основной для СНГ)
"""
from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.types import (
    CallbackQuery, LabeledPrice, PreCheckoutQuery, Message
)
from aiogram import Bot

from services.database import update_user, AsyncSessionLocal, Payment, User
from keyboards.kb import after_reading_kb
from config import config
from sqlalchemy import select

router = Router()

# Конфигурация продуктов (Telegram Stars)
PRODUCTS = {
    "single": {
        "title": "✨ Один расклад Таро",
        "description": "Персональный расклад от Алины с изображением карт",
        "stars": config.STARS_SINGLE_SPREAD,
        "payload": "single_spread",
    },
    "base": {
        "title": "📦 Базовая подписка — 1 месяц",
        "description": "5 раскладов в месяц: Таро, гороскоп, совместимость",
        "stars": config.STARS_MONTHLY_BASE,
        "payload": "base_subscription",
    },
    "premium": {
        "title": "👑 Премиум подписка — 1 месяц",
        "description": "Безлимитные расклады + кельтский крест + приоритет",
        "stars": config.STARS_MONTHLY_PREMIUM,
        "payload": "premium_subscription",
    },
}


async def send_invoice_stars(chat_id: int, product_key: str, bot: Bot):
    """Отправляем инвойс через Telegram Stars"""
    product = PRODUCTS[product_key]
    prices = [LabeledPrice(label=product["title"], amount=product["stars"])]

    await bot.send_invoice(
        chat_id=chat_id,
        title=product["title"],
        description=product["description"],
        payload=product["payload"],
        currency="XTR",          # XTR = Telegram Stars
        prices=prices,
        protect_content=False,
    )


# ==================== ОБРАБОТЧИКИ КНОПОК ====================

@router.callback_query(F.data == "buy_stars_single")
async def buy_single_stars(callback: CallbackQuery):
    from config import config
    bot = Bot(token=config.BOT_TOKEN)
    await send_invoice_stars(callback.message.chat.id, "single", bot)
    await bot.session.close()
    await callback.answer()


@router.callback_query(F.data == "buy_stars_base")
async def buy_base_stars(callback: CallbackQuery):
    from config import config
    bot = Bot(token=config.BOT_TOKEN)
    await send_invoice_stars(callback.message.chat.id, "base", bot)
    await bot.session.close()
    await callback.answer()


@router.callback_query(F.data == "buy_stars_premium")
async def buy_premium_stars(callback: CallbackQuery):
    from config import config
    bot = Bot(token=config.BOT_TOKEN)
    await send_invoice_stars(callback.message.chat.id, "premium", bot)
    await bot.session.close()
    await callback.answer()


# ==================== PRE-CHECKOUT ====================

@router.pre_checkout_query()
async def pre_checkout(pre_checkout_query: PreCheckoutQuery):
    """Подтверждаем платёж"""
    await pre_checkout_query.answer(ok=True)


# ==================== SUCCESSFUL PAYMENT ====================

@router.message(F.successful_payment)
async def successful_payment(message: Message):
    """Обработка успешного платежа"""
    payment = message.successful_payment
    payload = payment.invoice_payload
    user_id = message.from_user.id

    # Записываем платёж
    async with AsyncSessionLocal() as session:
        payment_record = Payment(
            user_id=user_id,
            payment_id=payment.telegram_payment_charge_id,
            payment_type=payload,
            amount=payment.total_amount,
            currency=payment.currency,
            status="success"
        )
        session.add(payment_record)
        await session.commit()

    # Активируем подписку
    now = datetime.utcnow()

    if payload == "single_spread":
        # Добавляем 1 бесплатный расклад (хак через total_spreads_free обнуление)
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == user_id)
            )
            user = result.scalar_one_or_none()
            if user and user.total_spreads_free >= config.FREE_SPREADS_TOTAL:
                # Если лимит исчерпан — временно даём доступ через "base" на 1 использование
                user.subscription_type = "base"
                user.subscription_expires = now + timedelta(hours=1)
                user.spreads_used_this_month = 0
                user.spreads_month = now.month
                await session.commit()

        success_text = (
            "✅ *Оплата прошла успешно!*\n\n"
            "✨ Ваш расклад доступен. Возвращайтесь в меню и выбирайте расклад!\n\n"
            "🔮 _Алина ждёт вас..._"
        )

    elif payload == "base_subscription":
        expires = now + timedelta(days=31)
        await update_user(user_id,
                          subscription_type="base",
                          subscription_expires=expires,
                          spreads_used_this_month=0,
                          spreads_month=now.month)
        success_text = (
            "✅ *Базовая подписка активирована!*\n\n"
            "📦 У вас 5 раскладов в этом месяце\n"
            f"📅 Действует до: {expires.strftime('%d.%m.%Y')}\n\n"
            "🔮 _Выбирайте расклад в главном меню!_"
        )

    elif payload == "premium_subscription":
        expires = now + timedelta(days=31)
        await update_user(user_id,
                          subscription_type="premium",
                          subscription_expires=expires)
        success_text = (
            "✅ *Премиум подписка активирована!*\n\n"
            "👑 Безлимитные расклады весь месяц\n"
            f"📅 Действует до: {expires.strftime('%d.%m.%Y')}\n\n"
            "🔮 _Звёзды полностью открыты для вас!_"
        )
    else:
        success_text = "✅ Оплата успешна! Возвращайтесь в меню."

    await message.answer(
        success_text,
        parse_mode="Markdown",
        reply_markup=after_reading_kb()
    )
