"""
Только календарь-картинка. Всё остальное — в caption.
"""
from io import BytesIO
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont
import os

COLOR_DONE = "#4CAF50"
COLOR_EMPTY = "#EBEDF0"
COLOR_FUTURE = "#F5F5F5"
COLOR_BG = "#FFFFFF"
COLOR_MUTED = "#8B949E"

CELL_SIZE = 22
CELL_GAP = 4
PADDING = 16
LABEL_WIDTH = 32
TOP_MONTH_HEIGHT = 16


def _get_font(size: int, bold: bool = False):
    """Roboto (с fallback на DejaVu)."""
    roboto_paths = [
        f"/usr/share/fonts/truetype/roboto/unhinted/Roboto-{'Bold' if bold else 'Regular'}.ttf",
        f"/usr/share/fonts/truetype/roboto/Roboto-{'Bold' if bold else 'Regular'}.ttf",
        f"/usr/share/fonts/truetype/roboto/hinted/Roboto-{'Bold' if bold else 'Regular'}.ttf",
    ]
    dejavu_paths = [
        f"/usr/share/fonts/truetype/dejavu/DejaVuSans{'-Bold' if bold else ''}.ttf",
    ]
    for path in roboto_paths + dejavu_paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def render_calendar(done_dates: set, weeks: int = 8) -> BytesIO:
    """Рисует компактный календарь: месяц сверху, дни недели слева."""
    today = datetime.now().date()
    monday = today - timedelta(days=today.weekday())
    start_monday = monday - timedelta(weeks=weeks - 1)

    font_small = _get_font(11)

    width = PADDING * 2 + LABEL_WIDTH + weeks * (CELL_SIZE + CELL_GAP) - CELL_GAP
    height = PADDING * 2 + TOP_MONTH_HEIGHT + 7 * (CELL_SIZE + CELL_GAP) - CELL_GAP

    img = Image.new("RGB", (width, height), COLOR_BG)
    draw = ImageDraw.Draw(img)

    # Подписи месяцев сверху
    month_names = ["янв", "фев", "мар", "апр", "май", "июн",
                   "июл", "авг", "сен", "окт", "ноя", "дек"]
    last_month = None
    for w in range(weeks):
        week_start = start_monday + timedelta(weeks=w)
        if week_start.month != last_month:
            x = PADDING + LABEL_WIDTH + w * (CELL_SIZE + CELL_GAP)
            draw.text((x, PADDING), month_names[week_start.month - 1],
                      fill=COLOR_MUTED, font=font_small)
            last_month = week_start.month

    # Дни недели слева
    day_labels = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    y0 = PADDING + TOP_MONTH_HEIGHT
    for d, name in enumerate(day_labels):
        y = y0 + d * (CELL_SIZE + CELL_GAP) + 5
        draw.text((PADDING, y), name, fill=COLOR_MUTED, font=font_small)

    # Сетка
    for d in range(7):
        for w in range(weeks):
            day = start_monday + timedelta(weeks=w, days=d)
            x = PADDING + LABEL_WIDTH + w * (CELL_SIZE + CELL_GAP)
            y = y0 + d * (CELL_SIZE + CELL_GAP)

            if day > today:
                color = COLOR_FUTURE
            elif day.strftime("%Y-%m-%d") in done_dates:
                color = COLOR_DONE
            else:
                color = COLOR_EMPTY

            draw.rounded_rectangle(
                [x, y, x + CELL_SIZE, y + CELL_SIZE],
                radius=4,
                fill=color,
            )

    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf