"""
Генерация картинки с календарём активности.
Использует Pillow для рендера зелёных квадратиков (как в GitHub-контрибуциях).
"""
from io import BytesIO
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont

# Цвета
COLOR_DONE = "#4CAF50"       # зелёный — выполнен
COLOR_EMPTY = "#E0E0E0"      # серый — не выполнен
COLOR_FUTURE = "#F5F5F5"     # светлый — будущее
COLOR_BG = "#FFFFFF"         # фон
COLOR_TEXT = "#666666"       # цвет текста

CELL_SIZE = 28
CELL_GAP = 4
LEFT_MARGIN = 50
TOP_MARGIN = 45
BOTTOM_MARGIN = 40
RIGHT_MARGIN = 20


def _get_font(size: int):
    """Пробует найти системный шрифт, иначе — дефолтный."""
    candidates = [
        "DejaVuSans.ttf",
        "Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default()


def render_calendar(done_dates: set, weeks: int = 8) -> BytesIO:
    """Рисует календарь активности и возвращает PNG в BytesIO."""
    width = LEFT_MARGIN + weeks * (CELL_SIZE + CELL_GAP) + RIGHT_MARGIN
    height = TOP_MARGIN + 7 * (CELL_SIZE + CELL_GAP) + BOTTOM_MARGIN

    img = Image.new("RGB", (width, height), COLOR_BG)
    draw = ImageDraw.Draw(img)

    font = _get_font(15)
    font_small = _get_font(12)

    # Заголовок
    today = datetime.now().date()
    monday = today - timedelta(days=today.weekday())
    start_monday = monday - timedelta(weeks=weeks - 1)
    end_date = start_monday + timedelta(weeks=weeks - 1, days=6)

    period = f"{start_monday.strftime('%d.%m')} — {end_date.strftime('%d.%m')}"
    draw.text((LEFT_MARGIN, 12), f"Активность: {period}", fill=COLOR_TEXT, font=font)

    # Дни недели слева
    day_names = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    for d, name in enumerate(day_names):
        y = TOP_MARGIN + d * (CELL_SIZE + CELL_GAP) + 6
        draw.text((12, y), name, fill=COLOR_TEXT, font=font_small)

    # Сетка
    for d in range(7):
        for w in range(weeks):
            day = start_monday + timedelta(weeks=w, days=d)
            x = LEFT_MARGIN + w * (CELL_SIZE + CELL_GAP)
            y = TOP_MARGIN + d * (CELL_SIZE + CELL_GAP)

            if day > today:
                color = COLOR_FUTURE
            elif day.strftime("%Y-%m-%d") in done_dates:
                color = COLOR_DONE
            else:
                color = COLOR_EMPTY

            draw.rounded_rectangle(
                [x, y, x + CELL_SIZE, y + CELL_SIZE],
                radius=6,
                fill=color,
            )

    # Подпись
    draw.text(
        (LEFT_MARGIN, height - 24),
        "SkillUp Coach",
        fill=COLOR_TEXT,
        font=font_small,
    )

    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf