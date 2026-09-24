"""
Единая картинка со статистикой и календарём (как Habit Otter).
Всё в одном изображении — единый шрифт.
"""
from io import BytesIO
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont
import os

COLOR_DONE = "#4CAF50"
COLOR_EMPTY = "#EBEDF0"
COLOR_FUTURE = "#F5F5F5"
COLOR_BG = "#FFFFFF"
COLOR_TITLE = "#1F2937"
COLOR_TEXT = "#4B5563"
COLOR_MUTED = "#9CA3AF"

CELL_SIZE = 20
CELL_GAP = 4
PADDING = 24
LABEL_WIDTH = 32


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


def render_stats(
    done_dates: set,
    weeks: int = 8,
    active_count: int = 0,
    total_done: int = 0,
    total_success: int = 0,
    current_streak: int = 0,
    best_streak: int = 0,
    skill_stats: list = None,
) -> BytesIO:
    """Рисует ВСЮ статистику одной картинкой."""
    if skill_stats is None:
        skill_stats = []

    font_title = _get_font(18, bold=True)
    font_stat = _get_font(13)
    font_small = _get_font(11)
    font_tiny = _get_font(10)

    # Ширина
    cal_width = LABEL_WIDTH + weeks * (CELL_SIZE + CELL_GAP) - CELL_GAP
    width = PADDING * 2 + max(cal_width, 300)

    # Высота — считаем заранее
    y = PADDING
    y += 26 + 12          # title
    y += 22               # строка 1
    y += 20               # строка 2
    y += 20               # строка 3
    y += 20               # строка 4
    y += 20               # строка 5
    y += 16
    y += 20               # "Активность по ..."
    y += 8
    y += 16               # месяцы сверху
    y += 7 * (CELL_SIZE + CELL_GAP) - CELL_GAP   # календарь
    y += 16
    y += 20               # легенда
    y += 16
    y += 20               # "По навыкам:"
    y += max(len(skill_stats), 1) * 20
    height = y + PADDING

    img = Image.new("RGB", (width, height), COLOR_BG)
    draw = ImageDraw.Draw(img)

    today = datetime.now().date()
    monday = today - timedelta(days=today.weekday())
    start_monday = monday - timedelta(weeks=weeks - 1)
    period = f"{start_monday.strftime('%d.%m')} — {today.strftime('%d.%m')}"

    y = PADDING

    # 1. Заголовок
    draw.text((PADDING, y), "Твоя статистика", fill=COLOR_TITLE, font=font_title)
    y += 26 + 12

    # 2. Метрики
    draw.text((PADDING, y), f"Активных навыков: {active_count}", fill=COLOR_TEXT, font=font_stat)
    y += 22
    draw.text((PADDING, y), f"Всего шагов: {total_done}", fill=COLOR_TEXT, font=font_stat)
    y += 20
    draw.text((PADDING, y), f"Звёзд собрано: {total_success}", fill=COLOR_TEXT, font=font_stat)
    y += 20
    draw.text((PADDING, y), f"Текущая серия: {current_streak} дн.", fill=COLOR_TEXT, font=font_stat)
    y += 20
    draw.text((PADDING, y), f"Лучшая серия: {best_streak} дн.", fill=COLOR_TEXT, font=font_stat)
    y += 20 + 16

    # 3. Активность
    draw.text((PADDING, y), f"Активность по {period}", fill=COLOR_TITLE, font=font_stat)
    y += 20 + 8

    # 4. Подписи месяцев
    month_names = ["янв", "фев", "мар", "апр", "май", "июн",
                   "июл", "авг", "сен", "окт", "ноя", "дек"]
    last_month = None
    for w in range(weeks):
        week_start = start_monday + timedelta(weeks=w)
        if week_start.month != last_month:
            x = PADDING + LABEL_WIDTH + w * (CELL_SIZE + CELL_GAP)
            draw.text((x, y), month_names[week_start.month - 1],
                      fill=COLOR_MUTED, font=font_tiny)
            last_month = week_start.month
    y += 16

    # 5. Дни недели слева
    day_labels = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    for d, name in enumerate(day_labels):
        label_y = y + d * (CELL_SIZE + CELL_GAP) + 4
        draw.text((PADDING, label_y), name, fill=COLOR_MUTED, font=font_small)

    # 6. Сетка
    for d in range(7):
        for w in range(weeks):
            day = start_monday + timedelta(weeks=w, days=d)
            x = PADDING + LABEL_WIDTH + w * (CELL_SIZE + CELL_GAP)
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

    y += 7 * (CELL_SIZE + CELL_GAP) - CELL_GAP + 16

    # 7. Легенда
    draw.rounded_rectangle(
        [PADDING, y, PADDING + 14, y + 14],
        radius=3, fill=COLOR_DONE,
    )
    draw.text((PADDING + 20, y - 1), "выполнено", fill=COLOR_TEXT, font=font_small)

    draw.rounded_rectangle(
        [PADDING + 110, y, PADDING + 124, y + 14],
        radius=3, fill=COLOR_EMPTY,
    )
    draw.text((PADDING + 130, y - 1), "не выполнено", fill=COLOR_TEXT, font=font_small)

    y += 16 + 20

    # 8. По навыкам
    draw.text((PADDING, y), "По навыкам:", fill=COLOR_TITLE, font=font_stat)
    y += 20

    if skill_stats:
        for s in skill_stats:
            line = f"• {s['name']} — {s['streak']} дн. | {s['percent']}%"
            draw.text((PADDING + 4, y), line, fill=COLOR_TEXT, font=font_small)
            y += 20
    else:
        draw.text((PADDING + 4, y), "— пока нет активных навыков",
                  fill=COLOR_MUTED, font=font_small)

    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf