"""
Генерация картинки с календарём активности.
Только сетка квадратиков — без текста (текст идёт в caption).
"""
from io import BytesIO
from datetime import datetime, timedelta
from PIL import Image, ImageDraw

# Цвета
COLOR_DONE = "#4CAF50"       # зелёный — выполнен
COLOR_EMPTY = "#EBEDF0"      # светло-серый — не выполнен
COLOR_FUTURE = "#F5F5F5"     # будущее (не наступило)
COLOR_BG = "#FFFFFF"

CELL_SIZE = 20
CELL_GAP = 4
PADDING = 16


def render_calendar(done_dates: set, weeks: int = 8) -> BytesIO:
    """Рисует сетку квадратиков и возвращает PNG в BytesIO."""
    width = PADDING * 2 + weeks * (CELL_SIZE + CELL_GAP) - CELL_GAP
    height = PADDING * 2 + 7 * (CELL_SIZE + CELL_GAP) - CELL_GAP

    img = Image.new("RGB", (width, height), COLOR_BG)
    draw = ImageDraw.Draw(img)

    today = datetime.now().date()
    monday = today - timedelta(days=today.weekday())
    start_monday = monday - timedelta(weeks=weeks - 1)

    for d in range(7):
        for w in range(weeks):
            day = start_monday + timedelta(weeks=w, days=d)
            x = PADDING + w * (CELL_SIZE + CELL_GAP)
            y = PADDING + d * (CELL_SIZE + CELL_GAP)

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