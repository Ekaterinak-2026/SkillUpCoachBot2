"""
Обработчик команды /digest.
Отправляет недельный дайджест вручную — удобно для тестирования
и для тех, кто хочет посмотреть статистику до воскресенья.
"""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from core import get_user, get_week_stats, get_week_stats_by_skill
import texts

router = Router()


@router.message(Command("digest"))
async def cmd_digest(message: Message) -> None:
    """Отправляет пользователю дайджест по запросу."""
    user_id = message.from_user.id
    user = await get_user(user_id)

    if not user or not user.get("skill"):
        await message.answer(texts.NOT_REGISTERED)
        return

    stats = await get_week_stats(user_id)
    skill_stats = await get_week_stats_by_skill(user_id)

    max_total = len(skill_stats) * 7
    if skill_stats:
        skills_text = "\n".join([
            f"• {s['name']} — {s['done']}/7 | {s['favorite_type']}"
            for s in skill_stats
        ])
    else:
        skills_text = "— пока нет активных навыков"

    text = texts.DIGEST_HEADER.format(name=user.get("username") or "друг")
    text += texts.DIGEST_BODY.format(
        done_total=stats["done_count"],
        max_total=max_total,
        best_streak=user["best_streak"],
        total=user["total_success"],
        skills_text=skills_text,
    )

    if user["best_streak"] >= 5:
        text += texts.DIGEST_TIP_LONG_STREAK.format(streak=user["best_streak"])
    elif stats["done_count"] < 3:
        text += texts.DIGEST_TIP_MANY_MISSES
    else:
        text += texts.DIGEST_TIP_DEFAULT

    await message.answer(text)