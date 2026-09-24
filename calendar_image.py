"""
Генерация картинки со статистикой.
Рисует заголовок + метрики + календарь.
"""
from io import BytesIO
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont
import os

COLOR_DONE = "#4CAF50"
COLOR_EMPTY = "#EBEDF0"
COLOR_FUTURE = "#F5F5F5"
COLOR_BG = "#FFFFFF"
COLOR_TITLE = "#24292F"
COLOR_TEXT = "#57606A"

CELL_SIZE = 22
CELL_GAP = 4
PADDING = 20


def _get_font(size: int, bold: bool = False):
    """Загружает системный DejaVuSans (устанавливается через Dockerfile)."""
    filename = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    paths = [
        f"/usr/share/fonts/truetype/dejavu/{filename}",
        f"/usr/share/fonts/TTF/{filename}",
    ]
    for path in paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def render_calendar(
    done_dates: set,
    weeks: int = 8,
    active_count: int = 0,
    total_done: int = 0,
    total_success: int = 0,
    current_streak: int = 0,
    best_streak: int = 0,
) -> BytesIO:
    """Рисует картинку со статистикой и календарём."""
    today = datetime.now().date()
    monday = today - timedelta(days=today.weekday())
    start_monday = monday - timedelta(weeks=weeks - 1)

    calendar_width = weeks * (CELL_SIZE + CELL_GAP) - CELL_GAP
    width = PADDING * 2 + max(calendar_width, 280)

    font_title = _get_font(16, bold=True)
    font_stat = _get_font(13)

    top_block = 24 + 8 + 20 + 6 + 20 + 12 + 20 + 6
    cal_height = 7 * (CELL_SIZE + CELL_GAP) - CELL_GAP
    height = PADDING * 2 + top_block + cal_height

    img = Image.new("RGB", (width, height), COLOR_BG)
    draw = ImageDraw.Draw(img)

    y = PADDING

    # 1. Заголовок
    draw.text((PADDING, y), "Твоя статистика", fill=COLOR_TITLE, font=font_title)
    y += 24 + 8

    # 2. Метрики
    line1 = f"Активных: {active_count}     Всего шагов: {total_done}"
    line2 = f"Звёзд: {total_success}     Серия: {current_streak} дн. (лучшая: {best_streak})"
    draw.text((PADDING, y), line1, fill=COLOR_TEXT, font=font_stat)
    y += 20 + 6
    draw.text((PADDING, y), line2, fill=COLOR_TEXT, font=font_stat)
    y += 20 + 12

    # 3. Активность
    period = f"{start_monday.strftime('%d.%m')} — {today.strftime('%d.%m')}"
    draw.text((PADDING, y), f"Активность: {period}", fill=COLOR_TITLE, font=font_stat)
    y += 20 + 6

    # 4. Календарь
    for d in range(7):
        for w in range(weeks):
            day = start_monday + timedelta(weeks=w, days=d)
            x = PADDING + w * (CELL_SIZE + CELL_GAP)
            y_cell = y + d * (CELL_SIZE + CELL_GAP)

            if day > today:
                color = COLOR_FUTURE
            elif day.strftime("%Y-%m-%d") in done_dates:
                color = COLOR_DONE
            else:
                color = COLOR_EMPTY

            draw.rounded_rectangle(
                [x, y_cell, x + CELL_SIZE, y_cell + CELL_SIZE],
                radius=4,
                fill=color,
            )

    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf