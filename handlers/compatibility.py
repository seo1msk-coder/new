"""
Хендлер совместимости пар
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram import Bot

from services.ai_service import generate_compatibility
from services.database import can_use_spread, increment_spread_count
from keyboards.kb import compatibility_zodiac_kb, after_reading_kb, paywall_kb, ZODIAC_RU

router = Router()


@router.callback_query(F.data == "menu_compatibility")
async def show_compat_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "💕 *Совместимость пар*\n\n"
        "Выберите *ваш* знак зодиака:\n\n"
        "_Звёзды знают всё о вашей связи..._",
        parse_mode="Markdown",
        reply_markup=compatibility_zodiac_kb(step=1)
    )


@router.callback_query(F.data.startswith("compat1_"))
async def first_sign_selected(callback: CallbackQuery):
    sign1 = callback.data.replace("compat1_", "")
    sign1_name = ZODIAC_RU.get(sign1, sign1)

    await callback.message.edit_text(
        f"💕 *Совместимость пар*\n\n"
        f"Ваш знак: *{sign1_name}* ✓\n\n"
        f"Теперь выберите знак *партнёра*:",
        parse_mode="Markdown",
        reply_markup=compatibility_zodiac_kb(step=2, first_sign=sign1)
    )


@router.callback_query(F.data.startswith("compat2_"))
async def second_sign_selected(callback: CallbackQuery):
    # compat2_aries_scorpio
    parts = callback.data.replace("compat2_", "").split("_", 1)
    if len(parts) != 2:
        await callback.answer("Ошибка выбора")
        return

    sign1, sign2 = parts[0], parts[1]
    sign1_name = ZODIAC_RU.get(sign1, sign1)
    sign2_name = ZODIAC_RU.get(sign2, sign2)

    # Проверяем доступ
    can_use, reason = await can_use_spread(callback.from_user.id)
    if not can_use:
        await callback.message.edit_text(
            "🌙 *Анализ совместимости требует подписки*\n\n"
            "Первый бесплатный расклад уже использован...\n\n"
            "👑 Оформите подписку для доступа ко всем функциям.",
            parse_mode="Markdown",
            reply_markup=paywall_kb()
        )
        return

    loading_msg = await callback.message.edit_text(
        f"💕 *Алина анализирует вашу пару...*\n\n"
        f"🔮 {sign1_name} + {sign2_name}\n\n"
        f"✨ Звёзды раскрывают тайны вашей связи...\n"
        f"🌙 Чувствуйте энергию момента...",
        parse_mode="Markdown"
    )

    try:
        compat_text = await generate_compatibility(sign1_name, sign2_name)

        from config import config
        bot = Bot(token=config.BOT_TOKEN)

        try:
            await loading_msg.delete()
        except:
            pass

        header = f"💕 *Совместимость: {sign1_name} + {sign2_name}*\n\n"
        full_text = header + compat_text

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
            "compatibility",
            f"{sign1_name} + {sign2_name}",
            compat_text
        )

        await bot.session.close()

    except Exception as e:
        await loading_msg.edit_text(
            f"😔 Произошла ошибка: {str(e)[:100]}\n\nПопробуйте через минуту.",
            reply_markup=after_reading_kb()
        )
