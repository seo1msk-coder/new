"""
Генерация изображений карт Таро
Создаём красивые карточки с PIL (без внешних API — быстро и бесплатно)
"""
import io
import random
import math
from PIL import Image, ImageDraw, ImageFont
import requests
from pathlib import Path

ASSETS_DIR = Path(__file__).parent.parent / "assets"
ASSETS_DIR.mkdir(exist_ok=True)

# Цветовые схемы для разных карт
CARD_THEMES = {
    "major": {
        "bg_colors": [(15, 5, 35), (20, 10, 45), (10, 3, 28)],
        "accent": (180, 140, 60),
        "glow": (255, 200, 80),
    },
    "cups": {
        "bg_colors": [(5, 20, 45), (10, 25, 55)],
        "accent": (80, 150, 220),
        "glow": (120, 180, 255),
    },
    "wands": {
        "bg_colors": [(40, 15, 5), (55, 20, 8)],
        "accent": (220, 120, 40),
        "glow": (255, 160, 60),
    },
    "swords": {
        "bg_colors": [(15, 25, 35), (20, 30, 45)],
        "accent": (150, 190, 220),
        "glow": (180, 220, 255),
    },
    "pentacles": {
        "bg_colors": [(10, 30, 15), (15, 40, 20)],
        "accent": (80, 180, 100),
        "glow": (100, 220, 120),
    },
}

CARD_SYMBOLS = {
    "Шут": "☽✦☾",
    "Маг": "∞",
    "Жрица": "☽",
    "Императрица": "♀",
    "Император": "♂",
    "Иерофант": "✝",
    "Влюблённые": "♡",
    "Колесница": "⚡",
    "Сила": "∞",
    "Отшельник": "⌂",
    "Колесо Фортуны": "⊕",
    "Справедливость": "⚖",
    "Повешенный": "⬡",
    "Смерть": "☠",
    "Умеренность": "△",
    "Дьявол": "⛧",
    "Башня": "⚡",
    "Звезда": "✦",
    "Луна": "☽",
    "Солнце": "☀",
    "Суд": "♪",
    "Мир": "⊕",
}


def get_card_theme(card_name: str) -> dict:
    """Определяем тему по типу карты"""
    card_lower = card_name.lower()
    if any(suit in card_lower for suit in ["кубков", "чаш"]):
        return CARD_THEMES["cups"]
    elif any(suit in card_lower for suit in ["жезлов", "посохов"]):
        return CARD_THEMES["wands"]
    elif "мечей" in card_lower:
        return CARD_THEMES["swords"]
    elif "пентаклей" in card_lower:
        return CARD_THEMES["pentacles"]
    else:
        return CARD_THEMES["major"]


def draw_stars(draw: ImageDraw, width: int, height: int, count: int = 40):
    """Рисуем звёзды на фоне"""
    for _ in range(count):
        x = random.randint(0, width)
        y = random.randint(0, height)
        size = random.choice([1, 1, 1, 2, 2, 3])
        brightness = random.randint(150, 255)
        color = (brightness, brightness, int(brightness * 0.9))
        if size == 1:
            draw.point((x, y), fill=color)
        else:
            draw.ellipse([x-size//2, y-size//2, x+size//2, y+size//2], fill=color)


def draw_mystical_border(draw: ImageDraw, width: int, height: int, accent: tuple, margin: int = 15):
    """Красивая рамка с орнаментом"""
    # Внешняя рамка
    draw.rectangle([margin, margin, width-margin, height-margin],
                   outline=accent, width=2)
    # Внутренняя рамка
    inner = margin + 6
    draw.rectangle([inner, inner, width-inner, height-inner],
                   outline=(*accent[:3], 120), width=1)

    # Угловые украшения
    corner_size = 12
    corners = [
        (margin, margin),
        (width-margin-corner_size, margin),
        (margin, height-margin-corner_size),
        (width-margin-corner_size, height-margin-corner_size),
    ]
    for cx, cy in corners:
        draw.rectangle([cx, cy, cx+corner_size, cy+corner_size],
                       outline=accent, width=1)
        # Диагональ в углу
        draw.line([cx+2, cy+2, cx+corner_size-2, cy+corner_size-2], fill=accent, width=1)


def draw_glow_circle(img: Image, cx: int, cy: int, radius: int, color: tuple, alpha_max: int = 60):
    """Рисуем свечение вокруг символа"""
    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    steps = 8
    for i in range(steps, 0, -1):
        r = int(radius * i / steps)
        alpha = int(alpha_max * (1 - i/steps))
        draw.ellipse([cx-r, cy-r, cx+r, cy+r],
                     fill=(*color[:3], alpha))
    img_rgba = img.convert('RGBA')
    img_rgba = Image.alpha_composite(img_rgba, overlay)
    return img_rgba.convert('RGB')


def create_card_image(card_name: str, position: int = 1, total: int = 1, is_reversed: bool = False) -> io.BytesIO:
    """
    Создаёт красивое изображение карты Таро.
    Возвращает BytesIO с PNG изображением.
    """
    WIDTH, HEIGHT = 400, 680
    theme = get_card_theme(card_name)
    bg_color = random.choice(theme["bg_colors"])
    accent = theme["accent"]
    glow_color = theme["glow"]

    img = Image.new('RGB', (WIDTH, HEIGHT), bg_color)
    draw = ImageDraw.Draw(img)

    # --- Градиентный фон ---
    for y in range(HEIGHT):
        ratio = y / HEIGHT
        r = int(bg_color[0] + (bg_color[0] * 0.5) * ratio)
        g = int(bg_color[1] + (bg_color[1] * 0.5) * ratio)
        b = int(bg_color[2] + (bg_color[2] * 0.5) * ratio)
        r, g, b = min(r, 255), min(g, 255), min(b, 255)
        draw.line([(0, y), (WIDTH, y)], fill=(r, g, b))

    # --- Звёзды ---
    draw_stars(draw, WIDTH, HEIGHT, 60)

    # --- Мистический орнамент (арка) ---
    center_x = WIDTH // 2
    arc_y = 160
    arc_radius = 90
    for r in range(arc_radius, arc_radius + 3):
        alpha_val = int(180 - (r - arc_radius) * 60)
        color_arc = (*accent[:3],)
        draw.arc([center_x - r, arc_y - r, center_x + r, arc_y + r],
                 start=180, end=360, fill=color_arc, width=1)

    # --- Центральный символ ---
    symbol = CARD_SYMBOLS.get(card_name.split("(")[0].strip(), "✦")
    
    # Рисуем свечение
    img = draw_glow_circle(img, center_x, arc_y, 70, glow_color, alpha_max=80)
    draw = ImageDraw.Draw(img)

    # Рисуем символ (большой текст)
    try:
        font_symbol = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 72)
        font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
        font_sub = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
        font_pos = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 13)
    except:
        font_symbol = ImageFont.load_default()
        font_title = font_symbol
        font_sub = font_symbol
        font_pos = font_symbol

    # Символ карты
    bbox = draw.textbbox((0, 0), symbol, font=font_symbol)
    sym_w = bbox[2] - bbox[0]
    draw.text((center_x - sym_w//2, arc_y - 45), symbol, fill=glow_color, font=font_symbol)

    # --- Рамка ---
    draw_mystical_border(draw, WIDTH, HEIGHT, accent)

    # --- Декоративная линия сверху ---
    line_y = 290
    draw.line([(40, line_y), (WIDTH-40, line_y)], fill=accent, width=1)
    # Ромбик в центре линии
    cx, cy = center_x, line_y
    size = 5
    draw.polygon([(cx, cy-size), (cx+size, cy), (cx, cy+size), (cx-size, cy)], fill=accent)

    # --- Название карты ---
    clean_name = card_name.replace("(перевёрнутая)", "").strip()
    
    # Разбиваем длинные названия
    words = clean_name.split()
    if len(words) > 2:
        line1 = " ".join(words[:len(words)//2])
        line2 = " ".join(words[len(words)//2:])
    else:
        line1 = clean_name
        line2 = None

    title_y = 305
    bbox1 = draw.textbbox((0, 0), line1, font=font_title)
    draw.text((center_x - (bbox1[2]-bbox1[0])//2, title_y), line1,
              fill=(255, 240, 200), font=font_title)
    if line2:
        bbox2 = draw.textbbox((0, 0), line2, font=font_title)
        draw.text((center_x - (bbox2[2]-bbox2[0])//2, title_y + 28), line2,
                  fill=(255, 240, 200), font=font_title)
        title_y += 28

    # --- Перевёрнутая пометка ---
    if is_reversed:
        rev_text = "~ перевёрнутая ~"
        bbox_r = draw.textbbox((0, 0), rev_text, font=font_sub)
        draw.text((center_x - (bbox_r[2]-bbox_r[0])//2, title_y + 35), rev_text,
                  fill=(*accent[:3],), font=font_sub)

    # --- Декоративная линия снизу ---
    bottom_line_y = HEIGHT - 90
    draw.line([(40, bottom_line_y), (WIDTH-40, bottom_line_y)], fill=accent, width=1)
    cx2, cy2 = center_x, bottom_line_y
    draw.polygon([(cx2, cy2-size), (cx2+size, cy2), (cx2, cy2+size), (cx2-size, cy2)], fill=accent)

    # --- Позиция карты ---
    pos_text = f"Карта {position} из {total}"
    bbox_pos = draw.textbbox((0, 0), pos_text, font=font_pos)
    draw.text((center_x - (bbox_pos[2]-bbox_pos[0])//2, bottom_line_y + 10), pos_text,
              fill=(150, 140, 120), font=font_pos)

    # --- Подпись Алины ---
    alina_text = "🔮 Алина · ИИ Астролог"
    try:
        bbox_a = draw.textbbox((0, 0), alina_text, font=font_pos)
        draw.text((center_x - (bbox_a[2]-bbox_a[0])//2, HEIGHT - 35), alina_text,
                  fill=(*accent[:3],), font=font_pos)
    except:
        pass

    # --- Перевёрнуть изображение если карта перевёрнутая ---
    if is_reversed:
        img = img.rotate(180)

    # Сохраняем в BytesIO
    output = io.BytesIO()
    img.save(output, format='PNG', quality=95)
    output.seek(0)
    return output


def create_spread_collage(cards: list[str]) -> io.BytesIO:
    """
    Создаёт коллаж из нескольких карт для расклада.
    Возвращает горизонтальный или сетчатый коллаж.
    """
    card_width, card_height = 400, 680
    max_per_row = 3
    
    count = len(cards)
    cols = min(count, max_per_row)
    rows = math.ceil(count / cols)
    
    padding = 20
    total_width = cols * card_width + (cols + 1) * padding
    total_height = rows * card_height + (rows + 1) * padding
    
    # Тёмный фон коллажа
    collage = Image.new('RGB', (total_width, total_height), (8, 3, 18))
    draw_bg = ImageDraw.Draw(collage)
    
    # Звёзды на фоне коллажа
    from services.card_generator import draw_stars
    draw_stars(draw_bg, total_width, total_height, 100)
    
    for i, card_name in enumerate(cards):
        is_reversed = "перевёрнутая" in card_name.lower()
        card_img_bytes = create_card_image(card_name, position=i+1, total=count, is_reversed=is_reversed)
        card_img = Image.open(card_img_bytes)
        
        col = i % cols
        row = i // cols
        x = padding + col * (card_width + padding)
        y = padding + row * (card_height + padding)
        
        collage.paste(card_img, (x, y))
    
    output = io.BytesIO()
    collage.save(output, format='PNG', quality=90)
    output.seek(0)
    return output
