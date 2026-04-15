"""
Хендлер раскладов Таро
"""
import asyncio
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from services.ai_service import generate_tarot_spread
from services.card_generator import create_card_image, create_spread_collage
from services.database import (
    get_or_create_user, can_use_spread, increment_spread_count,
    AsyncSessionLocal, User
)
from keyboards.kb import tarot_types_kb, skip_question_kb, after_reading_kb, paywall_kb
from sqlalchemy import select
import json

router = Router()


class TarotStates(StatesGroup):
    waiting_question = State()


SPREAD_NAMES = {
    "love": "💕 На любовь",
    "career": "💼 На карьеру",
    "day": "🌟 На день",
    "general": "🎯 На ситуацию",
    "celtic": "🔯 Кельтский крест",
}

PAYWALL_TEXT = """✨ *Ваш бесплатный расклад использован*

Звёзды хотят открыть вам больше... но для этого нужна подписка 🌙

*Что вы получите:*
📦 *Базовая (200 ⭐/мес)* — 5 раскладов в месяц
👑 *Премиум (400 ⭐/мес)* — безлимит + приоритет

*Или пригласите друга* — получите бесплатный расклад 🎁

_Звёзды терпеливы, но возможности приходят и уходят..._"""


@router.callback_query(F.data == "menu_tarot")
async def show_tarot_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "🃏 *Расклады Таро*\n\nКакой расклад хотите получить?\n\n_Каждая карта — послание Вселенной..._",
        parse_mode="Markdown",
        reply_markup=tarot_types_kb()
    )


@router.callback_query(F.data.startswith("tarot_"))
async def tarot_type_selected(callback: CallbackQuery, state: FSMContext):
    spread_type = callback.data.replace("tarot_", "")

    # Проверяем доступ
    can_use, reason = await can_use_spread(callback.from_user.id)
    if not can_use:
        await callback.message.edit_text(
            PAYWALL_TEXT,
            parse_mode="Markdown",
            reply_markup=paywall_kb()
        )
        return

    await state.update_data(spread_type=spread_type)

    spread_name = SPREAD_NAMES.get(spread_type, "Расклад")
    
    if spread_type == "day":
        # Для расклада на день вопрос не нужен
        await state.update_data(question="Что несёт мне сегодняшний день?")
        await do_tarot_spread(callback, state)
        return

    await callback.message.edit_text(
        f"🔮 *{spread_name}*\n\n"
        f"Сосредоточьтесь... Задайте свой вопрос Вселенной.\n\n"
        f"_Напишите вопрос или нажмите «Без вопроса» для общего расклада:_",
        parse_mode="Markdown",
        reply_markup=skip_question_kb()
    )
    await state.set_state(TarotStates.waiting_question)


@router.message(TarotStates.waiting_question)
async def receive_question(message: Message, state: FSMContext):
    await state.update_data(question=message.text)
    await do_tarot_spread_message(message, state)


@router.callback_query(F.data == "skip_question")
async def skip_question(callback: CallbackQuery, state: FSMContext):
    await state.update_data(question="Покажи общую картину моей жизни сейчас")
    await do_tarot_spread(callback, state)


async def do_tarot_spread(callback: CallbackQuery, state: FSMContext):
    """Запускает расклад из callback"""
    data = await state.get_data()
    spread_type = data.get("spread_type", "general")
    question = data.get("question", "")

    await state.clear()

    # Показываем анимацию ожидания
    loading_msg = await callback.message.edit_text(
        "🔮 *Алина перетасовывает колоду...*\n\n"
        "✨ Звёзды выстраиваются в нужном порядке\n"
        "🕯️ Энергия концентрируется...\n\n"
        "_Пожалуйста, подождите_ 🌙",
        parse_mode="Markdown"
    )

    await _process_spread(callback.message.chat.id, callback.from_user.id,
                          spread_type, question, loading_msg)


async def do_tarot_spread_message(message: Message, state: FSMContext):
    """Запускает расклад из сообщения"""
    data = await state.get_data()
    spread_type = data.get("spread_type", "general")
    question = data.get("question", "")

    await state.clear()

    loading_msg = await message.answer(
        "🔮 *Алина перетасовывает колоду...*\n\n"
        "✨ Звёзды выстраиваются в нужном порядке\n"
        "🕯️ Энергия концентрируется...\n\n"
        "_Пожалуйста, подождите_ 🌙",
        parse_mode="Markdown"
    )

    await _process_spread(message.chat.id, message.from_user.id,
                          spread_type, question, loading_msg)


async def _process_spread(chat_id: int, user_id: int, spread_type: str,
                           question: str, loading_msg):
    """Основная логика генерации расклада"""
    from aiogram import Bot
    from config import config

    # Получаем данные пользователя
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.telegram_id == user_id))
        user = result.scalar_one_or_none()

    user_data = {}
    if user:
        user_data = {
            "birth_date": str(user.birth_date) if user.birth_date else None,
            "zodiac_sign": user.zodiac_sign,
        }

    try:
        # Генерируем расклад через ИИ
        reading_text, cards = await generate_tarot_spread(spread_type, question, user_data)

        # Генерируем изображения карт
        if len(cards) == 1:
            is_rev = "перевёрнутая" in cards[0].lower()
            card_img = create_card_image(cards[0], 1, 1, is_rev)
            image_data = card_img.read()
        else:
            collage = create_spread_collage(cards)
            image_data = collage.read()

        # Формируем текст
        spread_name = SPREAD_NAMES.get(spread_type, "Расклад")
        cards_list = "\n".join([f"  {i+1}. *{c}*" for i, c in enumerate(cards)])

        header = f"🔮 *{spread_name}*\n"
        if question and question != "Покажи общую картину моей жизни сейчас":
            header += f"❓ Ваш вопрос: _{question}_\n"
        header += f"\n🃏 *Выпавшие карты:*\n{cards_list}\n\n"
        header += "─" * 30 + "\n\n"

        full_text = header + reading_text

        # Разбиваем если текст длинный (лимит TG — 4096 символов)
        bot = Bot(token=config.BOT_TOKEN)
        
        # Удаляем сообщение загрузки
        try:
            await loading_msg.delete()
        except:
            pass

        # Отправляем изображение карт
        photo_input = BufferedInputFile(image_data, filename="tarot_spread.png")
        
        # Первая часть с изображением
        if len(full_text) > 1000:
            caption_text = header + "_Расклад ниже_ 👇"
            rest_text = reading_text
        else:
            caption_text = full_text
            rest_text = None

        sent_photo = await bot.send_photo(
            chat_id=chat_id,
            photo=photo_input,
            caption=caption_text[:1024],
            parse_mode="Markdown"
        )

        # Отправляем полный текст расклада
        if rest_text:
            # Разбиваем на части по 4000 символов
            chunks = [rest_text[i:i+4000] for i in range(0, len(rest_text), 4000)]
            for i, chunk in enumerate(chunks):
                kb = after_reading_kb() if i == len(chunks) - 1 else None
                await bot.send_message(
                    chat_id=chat_id,
                    text=chunk,
                    parse_mode="Markdown",
                    reply_markup=kb
                )
        else:
            await bot.send_message(
                chat_id=chat_id,
                text="✨ _Расклад завершён. Что хотите сделать дальше?_",
                parse_mode="Markdown",
                reply_markup=after_reading_kb()
            )

        # Сохраняем в историю и инкрементим счётчик
        await increment_spread_count(
            user_id, spread_type, question, reading_text,
            cards=json.dumps(cards, ensure_ascii=False)
        )

        await bot.session.close()

    except Exception as e:
        try:
            await loading_msg.edit_text(
                f"😔 *Произошла ошибка*\n\n"
                f"Алина временно недоступна. Попробуйте через минуту.\n\n"
                f"_Ошибка: {str(e)[:100]}_",
                parse_mode="Markdown",
                reply_markup=after_reading_kb()
            )
        except:
            pass
