# 🔮 ИИ Астролог — Telegram Bot

Полноценный Telegram бот-астролог с раскладами Таро, гороскопами и анализом совместимости.
Монетизация через Telegram Stars (встроенная оплата в TG, работает в СНГ без ограничений).

---

## 🗂 Структура проекта

```
astro_bot/
├── bot.py                    # Точка входа
├── config.py                 # Конфигурация
├── requirements.txt
├── .env.example              # Шаблон переменных окружения
├── handlers/
│   ├── start.py              # /start, главное меню, профиль
│   ├── tarot.py              # Расклады Таро (все типы)
│   ├── horoscope.py          # Гороскопы (день/неделя/месяц)
│   ├── compatibility.py      # Совместимость пар
│   ├── subscription.py       # Тарифы, рефералы
│   └── payment.py            # Telegram Stars оплата
├── services/
│   ├── ai_service.py         # Claude + OpenAI интеграция
│   ├── card_generator.py     # Генерация изображений карт (PIL)
│   └── database.py           # SQLAlchemy модели + хелперы
└── keyboards/
    └── kb.py                 # Все кнопки и клавиатуры
```

---

## 🚀 Быстрый старт

### 1. Создайте бота в Telegram

1. Напишите [@BotFather](https://t.me/BotFather)
2. `/newbot` → задайте имя и username
3. Скопируйте токен

### 2. Клонируйте и настройте

```bash
git clone <your-repo>
cd astro_bot

# Создайте .env файл
cp .env.example .env
nano .env  # заполните токены
```

### 3. Установите зависимости

```bash
pip install -r requirements.txt
```

### 4. Запустите

```bash
python bot.py
```

---

## ⚙️ Конфигурация (.env)

| Переменная | Описание | Обязательно |
|---|---|---|
| `BOT_TOKEN` | Токен от BotFather | ✅ |
| `ANTHROPIC_API_KEY` | Claude API (Anthropic) | Один из двух |
| `OPENAI_API_KEY` | OpenAI GPT-4 API | Один из двух |
| `ADMIN_IDS` | Telegram ID администраторов | ✅ |
| `USE_TELEGRAM_STARS` | true/false (рекомендуется true) | — |

---

## 💳 Монетизация

### Telegram Stars (рекомендуется для СНГ)
- Встроенная оплата в Telegram
- Работает без иностранных карт
- Не требует регистрации юр. лица
- Комиссия Telegram: 30% (Stars уже учитывают это)

**Цены:**
| Тариф | Stars | ~₽ |
|---|---|---|
| 1 расклад | 75 ⭐ | ~150₽ |
| Базовая/мес | 200 ⭐ | ~400₽ |
| Премиум/мес | 400 ⭐ | ~800₽ |

### Для включения Stars в боте:
1. Откройте BotFather → ваш бот
2. `Bot Settings` → `Payments` → `Telegram Stars`
3. Готово! Оплата уже настроена в коде.

---

## 🃏 Функционал

### Расклады Таро
- 💕 На любовь (3 карты)
- 💼 На карьеру (3 карты)
- 🌟 На день (1 карта)
- 🎯 На ситуацию (3 карты)
- 🔯 Кельтский крест (10 карт) — Премиум

### Гороскоп
- 12 знаков зодиака
- Периоды: день / неделя / месяц

### Совместимость
- Анализ пары по знакам зодиака
- Процент совместимости
- Детальный разбор по блокам

### Монетизация
- 1 бесплатный расклад для новых пользователей
- Telegram Stars оплата
- Реферальная программа

---

## 🖥 Деплой на сервер (VPS)

### Вариант 1: systemd (рекомендуется)

```bash
# Создайте сервис
sudo nano /etc/systemd/system/astro-bot.service
```

```ini
[Unit]
Description=Astro Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/astro_bot
ExecStart=/usr/bin/python3 /home/ubuntu/astro_bot/bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable astro-bot
sudo systemctl start astro-bot
sudo systemctl status astro-bot
```

### Вариант 2: screen (для теста)

```bash
screen -S astro_bot
python bot.py
# Ctrl+A, D — выйти из screen
```

### Вариант 3: Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "bot.py"]
```

```bash
docker build -t astro-bot .
docker run -d --name astro-bot --env-file .env astro-bot
```

---

## 📊 Рекомендуемый хостинг для СНГ

| Провайдер | Цена | Подходит |
|---|---|---|
| [Aeza.net](https://aeza.net) | от 150₽/мес | ✅ Лучший для РФ |
| [Timeweb](https://timeweb.cloud) | от 199₽/мес | ✅ |
| [DigitalOcean](https://digitalocean.com) | от $4/мес | ✅ Международный |
| [Hetzner](https://hetzner.com) | от €4/мес | ✅ Дешёвый EU |

**Минимальные требования:** 1 CPU, 512MB RAM, Ubuntu 22.04

---

## 📈 Следующие шаги (Growth Hacking)

1. **Аналитика** — добавить отправку событий в PostHog или Mixpanel
2. **Рассылки** — ежедневный гороскоп подписчикам
3. **Реферальная программа** — автоматические начисления
4. **Персонаж Алина** — создать соц. сети, постить ИИ-видео
5. **A/B тест цен** — 75 vs 99 vs 149 Stars за расклад

---

## 🤝 Поддержка

Вопросы по настройке — создайте issue в репозитории.
