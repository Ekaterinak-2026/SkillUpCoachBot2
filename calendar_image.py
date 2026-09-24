"""
Генерация картинки с календарём активности.
Компактный стиль как в GitHub-контрибуциях.
"""
from io import BytesIO
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont
import os

# Цвета
COLOR_DONE = "#4CAF50"       # зелёный — выполнен
COLOR_EMPTY = "#EBEDF0"      # светло-серый — не выполнен
COLOR_FUTURE = "#F5F5F5"     # будущее (не наступило)
COLOR_BG = "#FFFFFF"         # фон
COLOR_TEXT = "#666666"       # цвет текста
COLOR_TITLE = "#24292F"      # цвет заголовка

CELL_SIZE = 18
CELL_GAP = 3
LEFT_MARGIN = 36
TOP_MARGIN = 48
BOTTOM_MARGIN = 36
RIGHT_MARGIN = 16


def _get_font(size: int):
    """Загружает DejaVuSans из папки проекта (с кириллицей)."""
    paths = [
        os.path.join(os.path.dirname(__file__), "fonts", "DejaVuSans.ttf"),
        "fonts/DejaVuSans.ttf",
        "/app/fonts/DejaVuSans.ttf",
    ]
    for path in paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def render_calendar(done_dates: set, weeks: int = 8) -> BytesIO:
    """Рисует компактный календарь активности и возвращает PNG в BytesIO."""
    width = LEFT_MARGIN + weeks * (CELL_SIZE + CELL_GAP) + RIGHT_MARGIN
    height = TOP_MARGIN + 7 * (CELL_SIZE + CELL_GAP) + BOTTOM_MARGIN

    img = Image.new("RGB", (width, height), COLOR_BG)
    draw = ImageDraw.Draw(img)

    font_title = _get_font(13)
    font_small = _get_font(10)

    # Период
    today = datetime.now().date()
    monday = today - timedelta(days=today.weekday())
    start_monday = monday - timedelta(weeks=weeks - 1)

    period = f"{start_monday.strftime('%d.%m')} — {today.strftime('%d.%m')}"
    draw.text((LEFT_MARGIN, 8), f"Активность: {period}", fill=COLOR_TITLE, font=font_title)

    # Дни недели слева (только Пн, Ср, Пт — как в GitHub)
    day_names = {0: "Пн", 2: "Ср", 4: "Пт"}
    for d, name in day_names.items():
        y = TOP_MARGIN + d * (CELL_SIZE + CELL_GAP) + 3
        draw.text((6, y), name, fill=COLOR_TEXT, font=font_small)

    # Подписи месяцев сверху
    last_month = None
    for w in range(weeks):
        week_start = start_monday + timedelta(weeks=w)
        if week_start.month != last_month:
            month_names = ["янв", "фев", "мар", "апр", "май", "июн",
                           "июл", "авг", "сен", "окт", "ноя", "дек"]
            month_label = month_names[week_start.month - 1]
            x = LEFT_MARGIN + w * (CELL_SIZE + CELL_GAP)
            draw.text((x, 26), month_label, fill=COLOR_TEXT, font=font_small)
            last_month = week_start.month

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
                radius=3,
                fill=color,
            )

    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf