"""
ИИ сервис — генерация раскладов через Claude / OpenAI
"""
import anthropic
import openai
import random
from config import config

# Инициализация клиентов
claude_client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY) if config.ANTHROPIC_API_KEY else None
openai_client = openai.AsyncOpenAI(api_key=config.OPENAI_API_KEY) if config.OPENAI_API_KEY else None

# ==================== КАРТЫ ТАРО ====================

MAJOR_ARCANA = [
    ("Шут", "0", "🃏"),
    ("Маг", "I", "🎩"),
    ("Жрица", "II", "🌙"),
    ("Императрица", "III", "🌹"),
    ("Император", "IV", "👑"),
    ("Иерофант", "V", "⛪"),
    ("Влюблённые", "VI", "💕"),
    ("Колесница", "VII", "⚡"),
    ("Сила", "VIII", "🦁"),
    ("Отшельник", "IX", "🕯️"),
    ("Колесо Фортуны", "X", "🎡"),
    ("Справедливость", "XI", "⚖️"),
    ("Повешенный", "XII", "🌀"),
    ("Смерть", "XIII", "🌑"),
    ("Умеренность", "XIV", "💧"),
    ("Дьявол", "XV", "🔥"),
    ("Башня", "XVI", "⚡"),
    ("Звезда", "XVII", "⭐"),
    ("Луна", "XVIII", "🌕"),
    ("Солнце", "XIX", "☀️"),
    ("Суд", "XX", "📯"),
    ("Мир", "XXI", "🌍"),
]

MINOR_ARCANA_SUITS = ["Жезлов", "Кубков", "Мечей", "Пентаклей"]
MINOR_ARCANA_VALUES = ["Туз", "Двойка", "Тройка", "Четвёрка", "Пятёрка",
                        "Шестёрка", "Семёрка", "Восьмёрка", "Девятка", "Десятка",
                        "Паж", "Рыцарь", "Королева", "Король"]

ALL_CARDS = [f"{name} {emoji}" for name, _, emoji in MAJOR_ARCANA] + \
            [f"{val} {suit}" for suit in MINOR_ARCANA_SUITS for val in MINOR_ARCANA_VALUES]


def draw_cards(count: int) -> list[str]:
    """Тянем карты случайно (с учётом перевёрнутых)"""
    cards = random.sample(ALL_CARDS, count)
    result = []
    for card in cards:
        if random.random() < 0.3:  # 30% шанс перевёрнутой
            result.append(f"{card} (перевёрнутая)")
        else:
            result.append(card)
    return result


# ==================== ПРОМПТЫ ====================

ALINA_PERSONA = """Ты — Алина, мистический ИИ-астролог с многолетним опытом.
Твой стиль: тёплый, загадочный, говоришь как живой человек — с паузами, метафорами, лёгким драматизмом.
Пишешь на русском языке. Используй редкие эмодзи для атмосферы (🌙✨🔮🕯️💫).
Никогда не говоришь что ты ИИ. Ты — Алина, живой человек-астролог.
Структурируй ответ красиво: используй разделители, абзацы.
Делай расклад ощущением живого, личного послания — как будто ты видишь человека лично."""


def build_tarot_prompt(spread_type: str, question: str, cards: list[str], user_data: dict) -> str:
    birth_info = ""
    if user_data.get("birth_date"):
        birth_info = f"Дата рождения: {user_data['birth_date']}, знак: {user_data.get('zodiac_sign', 'не указан')}."

    spreads = {
        "love": "расклад на любовь и отношения (3 карты: прошлое отношений, настоящее, будущее)",
        "career": "расклад на карьеру и деньги (3 карты: текущая ситуация, препятствие, совет)",
        "day": "расклад на день (1 карта: послание дня)",
        "celtic": "кельтский крест (10 карт: полный анализ ситуации)",
        "general": "общий расклад на ситуацию (3 карты: суть, совет, исход)",
    }

    spread_desc = spreads.get(spread_type, "общий расклад (3 карты)")
    cards_text = "\n".join([f"  {i+1}. {card}" for i, card in enumerate(cards)])

    return f"""{ALINA_PERSONA}

Сделай {spread_desc}.
{birth_info}
Вопрос пользователя: "{question}"

Выпавшие карты:
{cards_text}

Напиши развёрнутый, атмосферный расклад. Разбери каждую карту отдельно, потом дай общее послание.
В конце — конкретный совет на ближайшие 7 дней.
Объём: 400-600 слов. Пиши как живой человек, не как робот."""


def build_horoscope_prompt(zodiac: str, period: str, birth_date: str = None) -> str:
    periods = {
        "today": "на сегодня",
        "week": "на эту неделю",
        "month": "на этот месяц",
    }
    period_str = periods.get(period, "на сегодня")

    return f"""{ALINA_PERSONA}

Составь персональный гороскоп для знака {zodiac} {period_str}.
{"Дата рождения: " + birth_date if birth_date else ""}

Раздели на блоки:
💕 Любовь и отношения
💰 Финансы и карьера  
🌿 Здоровье и энергия
✨ Общий совет

Пиши живо, конкретно, с предсказаниями. Объём: 300-400 слов."""


def build_compatibility_prompt(sign1: str, sign2: str, name1: str = None, name2: str = None) -> str:
    p1 = name1 or sign1
    p2 = name2 or sign2

    return f"""{ALINA_PERSONA}

Сделай анализ совместимости пары: {p1} ({sign1}) и {p2} ({sign2}).

Раздели на блоки:
💕 Совместимость в любви (%)
🔥 Страсть и притяжение
💬 Общение и понимание  
⚡ Главные испытания пары
🌟 Ваши сильные стороны
🔮 Прогноз отношений

Дай процент совместимости и детальный разбор. Объём: 400-500 слов."""


# ==================== ВЫЗОВ API ====================

async def generate_with_claude(prompt: str) -> str:
    """Генерация через Claude (Anthropic)"""
    try:
        message = claude_client.messages.create(
            model="claude-opus-4-5",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text
    except Exception as e:
        raise Exception(f"Claude API error: {e}")


async def generate_with_openai(prompt: str) -> str:
    """Генерация через OpenAI GPT-4"""
    try:
        response = await openai_client.chat.completions.create(
            model="gpt-4o",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        raise Exception(f"OpenAI API error: {e}")


async def generate_reading(prompt: str) -> str:
    """Пробуем Claude, если нет — OpenAI"""
    if claude_client:
        try:
            return await generate_with_claude(prompt)
        except Exception:
            pass
    if openai_client:
        return await generate_with_openai(prompt)
    raise Exception("Нет доступных AI провайдеров")


# ==================== ПУБЛИЧНЫЕ ФУНКЦИИ ====================

async def generate_tarot_spread(
    spread_type: str,
    question: str,
    user_data: dict
) -> tuple[str, list[str]]:
    """Генерирует расклад Таро. Возвращает (текст, список_карт)"""
    card_counts = {"day": 1, "love": 3, "career": 3, "general": 3, "celtic": 10}
    count = card_counts.get(spread_type, 3)
    cards = draw_cards(count)
    prompt = build_tarot_prompt(spread_type, question, cards, user_data)
    text = await generate_reading(prompt)
    return text, cards


async def generate_horoscope(zodiac: str, period: str, birth_date: str = None) -> str:
    """Генерирует гороскоп"""
    prompt = build_horoscope_prompt(zodiac, period, birth_date)
    return await generate_reading(prompt)


async def generate_compatibility(sign1: str, sign2: str, name1: str = None, name2: str = None) -> str:
    """Генерирует совместимость пары"""
    prompt = build_compatibility_prompt(sign1, sign2, name1, name2)
    return await generate_reading(prompt)
