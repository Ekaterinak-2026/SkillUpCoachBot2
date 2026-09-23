"""
Работа с базой данных SQLite.
Используем глобальное соединение + WAL для стабильной работы в контейнерах.
"""
# v3.0 — force rebuild
# SkillUp Coach v2.0 — force rebuild

import aiosqlite
from datetime import datetime, timedelta
from typing import Optional

DB_NAME = "skillup.db"

_db: aiosqlite.Connection | None = None


async def _check_alive(db: aiosqlite.Connection) -> bool:
    """Проверяет, что соединение живое."""
    try:
        async with db.execute("SELECT 1") as cursor:
            await cursor.fetchone()
        return True
    except Exception:
        return False


async def get_db() -> aiosqlite.Connection:
    """Возвращает глобальное соединение, пересоздаёт при разрыве."""
    global _db

    # Если соединение есть и живое — используем
    if _db is not None and await _check_alive(_db):
        return _db

    # Иначе — закрываем старое и создаём новое
    if _db is not None:
        try:
            await _db.close()
        except Exception:
            pass

    _db = await aiosqlite.connect(DB_NAME)
    _db.row_factory = aiosqlite.Row
    await _db.execute("PRAGMA journal_mode=WAL")
    await _db.execute("PRAGMA synchronous=NORMAL")
    await _db.execute("PRAGMA busy_timeout=5000")
    return _db

# ============ ИНИЦИАЛИЗАЦИЯ ============

async def init_db() -> None:
    """Создаёт таблицы при первом запуске бота."""
    db = await get_db()

    await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            skill TEXT,
            timezone TEXT DEFAULT 'Europe/Moscow',
            morning_time TEXT DEFAULT '09:00',
            evening_time TEXT DEFAULT '20:00',
            streak INTEGER DEFAULT 0,
            best_streak INTEGER DEFAULT 0,
            total_success INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    await db.execute("""
        CREATE TABLE IF NOT EXISTS daily_steps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            skill_id INTEGER,
            date TEXT,
            step_type TEXT,
            status TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    """)

    await db.execute("""
        CREATE TABLE IF NOT EXISTS skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            archived_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    """)

    try:
        await db.execute(
            "ALTER TABLE users ADD COLUMN timezone TEXT DEFAULT 'Europe/Moscow'"
        )
    except Exception:
        pass

    try:
        await db.execute("ALTER TABLE daily_steps ADD COLUMN skill_id INTEGER")
    except Exception:
        pass

    # Миграция: добавляем колонку goal, если её нет
    try:
        await db.execute("ALTER TABLE users ADD COLUMN goal TEXT")
    except Exception:
        pass

    await db.commit()
    await _migrate_user_skills()


async def _migrate_user_skills() -> None:
    """Переносит старый users.skill в таблицу skills."""
    db = await get_db()
    async with db.execute("""
        SELECT u.user_id, u.skill FROM users u
        WHERE u.skill IS NOT NULL
        AND NOT EXISTS (SELECT 1 FROM skills s WHERE s.user_id = u.user_id)
    """) as cursor:
        rows = await cursor.fetchall()

    for user_id, skill_name in rows:
        await db.execute(
            "INSERT INTO skills (user_id, name, status) VALUES (?, ?, 'active')",
            (user_id, skill_name)
        )

    if rows:
        await db.commit()
        print(f"Миграция: перенесено {len(rows)} навыков пользователей")


# ============ ПОЛЬЗОВАТЕЛИ ============

async def add_user(user_id: int, username: str) -> None:
    db = await get_db()
    await db.execute(
        "INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)",
        (user_id, username)
    )
    await db.commit()


async def get_user(user_id: int) -> Optional[dict]:
    db = await get_db()
    async with db.execute(
        "SELECT * FROM users WHERE user_id = ?", (user_id,)
    ) as cursor:
        row = await cursor.fetchone()
        return dict(row) if row else None


async def update_user_skill(user_id: int, skill: str) -> None:
    db = await get_db()
    await db.execute(
        "UPDATE users SET skill = ?, streak = 0 WHERE user_id = ?",
        (skill, user_id)
    )
    await db.commit()


async def update_user_time(user_id: int, morning: str = None, evening: str = None) -> None:
    db = await get_db()
    if morning:
        await db.execute(
            "UPDATE users SET morning_time = ? WHERE user_id = ?",
            (morning, user_id)
        )
    if evening:
        await db.execute(
            "UPDATE users SET evening_time = ? WHERE user_id = ?",
            (evening, user_id)
        )
    await db.commit()


async def update_user_timezone(user_id: int, timezone: str) -> None:
    db = await get_db()
    await db.execute(
        "UPDATE users SET timezone = ? WHERE user_id = ?",
        (timezone, user_id)
    )
    await db.commit()


async def get_all_users() -> list[dict]:
    db = await get_db()
    async with db.execute("SELECT * FROM users") as cursor:
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


# ============ ЕЖЕДНЕВНЫЕ ШАГИ ============

async def save_daily_plan(user_id: int, step_type: str) -> None:
    today = datetime.now().strftime("%Y-%m-%d")
    db = await get_db()
    await db.execute(
        "DELETE FROM daily_steps WHERE user_id = ? AND date = ?",
        (user_id, today)
    )
    await db.execute(
        "INSERT INTO daily_steps (user_id, date, step_type, status) "
        "VALUES (?, ?, ?, 'запланирован')",
        (user_id, today, step_type)
    )
    await db.commit()


async def get_today_plan(user_id: int) -> Optional[dict]:
    today = datetime.now().strftime("%Y-%m-%d")
    db = await get_db()
    async with db.execute(
        "SELECT * FROM daily_steps WHERE user_id = ? AND date = ? "
        "ORDER BY id DESC LIMIT 1",
        (user_id, today)
    ) as cursor:
        row = await cursor.fetchone()
        return dict(row) if row else None


async def update_step_status(user_id: int, status: str) -> None:
    today = datetime.now().strftime("%Y-%m-%d")
    db = await get_db()
    await db.execute(
        "UPDATE daily_steps SET status = ? WHERE user_id = ? AND date = ?",
        (status, user_id, today)
    )
    await db.commit()


# ============ СЕРИЯ И СТАТИСТИКА ============

async def mark_step_done(user_id: int) -> dict:
    db = await get_db()
    await db.execute(
        "UPDATE users SET "
        "streak = streak + 1, "
        "total_success = total_success + 1 "
        "WHERE user_id = ?",
        (user_id,)
    )
    await db.execute(
        "UPDATE users SET best_streak = streak "
        "WHERE user_id = ? AND streak > best_streak",
        (user_id,)
    )
    await db.commit()
    async with db.execute(
        "SELECT * FROM users WHERE user_id = ?", (user_id,)
    ) as cursor:
        row = await cursor.fetchone()
        return dict(row) if row else {}


async def mark_step_failed(user_id: int) -> dict:
    db = await get_db()
    await db.execute(
        "UPDATE users SET streak = 0 WHERE user_id = ?", (user_id,)
    )
    await db.commit()
    async with db.execute(
        "SELECT * FROM users WHERE user_id = ?", (user_id,)
    ) as cursor:
        row = await cursor.fetchone()
        return dict(row) if row else {}


async def get_week_stats_by_skill(user_id: int) -> list[dict]:
    """Статистика за последние 7 дней по каждому активному навыку."""
    week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    skills = await get_active_skills(user_id)
    db = await get_db()
    result = []

    for s in skills:
        async with db.execute(
            "SELECT COUNT(*) as cnt FROM daily_steps "
            "WHERE user_id = ? AND skill_id = ? AND status = 'выполнен' AND date >= ?",
            (user_id, s["id"], week_ago)
        ) as cur:
            row = await cur.fetchone()
            done = row["cnt"] if row else 0

        async with db.execute(
            "SELECT step_type, COUNT(*) as cnt FROM daily_steps "
            "WHERE user_id = ? AND skill_id = ? AND status = 'выполнен' AND date >= ? "
            "GROUP BY step_type ORDER BY cnt DESC LIMIT 1",
            (user_id, s["id"], week_ago)
        ) as cur:
            row = await cur.fetchone()
            fav_type = row["step_type"] if row else "—"
            fav_count = row["cnt"] if row else 0

        result.append({
            "name": s["name"],
            "done": done,
            "favorite_type": fav_type,
            "favorite_count": fav_count,
        })

    return result

async def get_user_stats(user_id: int) -> dict:
    """Общая статистика: активные навыки, выполненные шаги, лучшая серия."""
    db = await get_db()

    async with db.execute(
        "SELECT COUNT(*) as cnt FROM daily_steps "
        "WHERE user_id = ? AND status = 'выполнен'",
        (user_id,)
    ) as cur:
        row = await cur.fetchone()
        total_done = row["cnt"] if row else 0

    active = await count_active_skills(user_id)

    async with db.execute(
        "SELECT best_streak, total_success FROM users WHERE user_id = ?",
        (user_id,)
    ) as cur:
        row = await cur.fetchone()
        best_streak = row["best_streak"] if row else 0
        total_success = row["total_success"] if row else 0

    return {
        "total_done": total_done,
        "active_count": active,
        "best_streak": best_streak,
        "total_success": total_success,
    }


async def get_current_streak(user_id: int) -> int:
    """Текущая серия: подряд идущие дни с хотя бы одним выполненным шагом."""
    db = await get_db()
    async with db.execute(
        "SELECT DISTINCT date FROM daily_steps "
        "WHERE user_id = ? AND status = 'выполнен' ORDER BY date DESC",
        (user_id,)
    ) as cur:
        rows = await cur.fetchall()

    if not rows:
        return 0

    dates = [r["date"] for r in rows]
    today = datetime.now().strftime("%Y-%m-%d")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    if dates[0] not in (today, yesterday):
        return 0

    streak = 0
    check = datetime.strptime(dates[0], "%Y-%m-%d")
    for d in dates:
        d_dt = datetime.strptime(d, "%Y-%m-%d")
        if d_dt == check:
            streak += 1
            check -= timedelta(days=1)
        elif d_dt < check:
            break
    return streak


async def get_activity_dates(user_id: int, days: int = 56) -> set:
    """Множество дат (YYYY-MM-DD) с выполненными шагами за последние N дней."""
    start = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    db = await get_db()
    async with db.execute(
        "SELECT DISTINCT date FROM daily_steps "
        "WHERE user_id = ? AND status = 'выполнен' AND date >= ?",
        (user_id, start)
    ) as cur:
        rows = await cur.fetchall()
    return {r["date"] for r in rows}


async def get_skill_stats(user_id: int) -> list[dict]:
    """По каждому активному навыку: серия и % за 30 дней."""
    skills = await get_active_skills(user_id)
    db = await get_db()
    thirty_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    today = datetime.now().strftime("%Y-%m-%d")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    result = []
    for s in skills:
        async with db.execute(
            "SELECT DISTINCT date FROM daily_steps "
            "WHERE user_id = ? AND skill_id = ? AND status = 'выполнен' "
            "ORDER BY date DESC",
            (user_id, s["id"])
        ) as cur:
            dates = [r["date"] for r in await cur.fetchall()]

        streak = 0
        if dates and dates[0] in (today, yesterday):
            check = datetime.strptime(dates[0], "%Y-%m-%d")
            for d in dates:
                d_dt = datetime.strptime(d, "%Y-%m-%d")
                if d_dt == check:
                    streak += 1
                    check -= timedelta(days=1)
                elif d_dt < check:
                    break

        async with db.execute(
            "SELECT COUNT(DISTINCT date) as cnt FROM daily_steps "
            "WHERE user_id = ? AND skill_id = ? AND status = 'выполнен' AND date >= ?",
            (user_id, s["id"], thirty_ago)
        ) as cur:
            row = await cur.fetchone()
            done_30 = row["cnt"] if row else 0

        percent = round(done_30 / 30 * 100)

        result.append({
            "name": s["name"],
            "streak": streak,
            "percent": percent,
        })

    return result
async def days_since_last_activity(user_id: int) -> int:
    db = await get_db()
    async with db.execute(
        "SELECT MAX(date) as last_date FROM daily_steps "
        "WHERE user_id = ? AND status = 'выполнен'",
        (user_id,)
    ) as cursor:
        row = await cursor.fetchone()
        last = row["last_date"] if row else None

    if not last:
        return 999

    try:
        last_dt = datetime.strptime(last, "%Y-%m-%d")
        return (datetime.now() - last_dt).days
    except Exception:
        return 999


async def reset_user(user_id: int) -> None:
    db = await get_db()
    await db.execute("DELETE FROM daily_steps WHERE user_id = ?", (user_id,))
    await db.execute("DELETE FROM skills WHERE user_id = ?", (user_id,))
    await db.execute(
        "UPDATE users SET skill = NULL, streak = 0, "
        "best_streak = 0, total_success = 0 WHERE user_id = ?",
        (user_id,)
    )
    await db.commit()


# ============ РАБОТА С НАВЫКАМИ ============

MAX_SKILLS = 5


async def add_skill(user_id: int, name: str) -> int:
    count = await count_active_skills(user_id)
    if count >= MAX_SKILLS:
        return -1

    db = await get_db()
    async with db.execute(
        "SELECT id FROM skills WHERE user_id = ? AND LOWER(name) = LOWER(?)",
        (user_id, name)
    ) as cursor:
        if await cursor.fetchone():
            return -2

    cursor = await db.execute(
        "INSERT INTO skills (user_id, name, status) VALUES (?, ?, 'active')",
        (user_id, name)
    )
    await db.commit()
    return cursor.lastrowid


async def get_active_skills(user_id: int) -> list[dict]:
    db = await get_db()
    async with db.execute(
        "SELECT * FROM skills WHERE user_id = ? AND status = 'active' ORDER BY id",
        (user_id,)
    ) as cursor:
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def get_archived_skills(user_id: int) -> list[dict]:
    db = await get_db()
    async with db.execute(
        "SELECT * FROM skills WHERE user_id = ? AND status = 'archived' ORDER BY id",
        (user_id,)
    ) as cursor:
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def get_skill_by_id(skill_id: int) -> dict | None:
    db = await get_db()
    async with db.execute(
        "SELECT * FROM skills WHERE id = ?", (skill_id,)
    ) as cursor:
        row = await cursor.fetchone()
        return dict(row) if row else None


async def count_active_skills(user_id: int) -> int:
    db = await get_db()
    async with db.execute(
        "SELECT COUNT(*) FROM skills WHERE user_id = ? AND status = 'active'",
        (user_id,)
    ) as cursor:
        row = await cursor.fetchone()
        return row[0] if row else 0


async def archive_skill(skill_id: int) -> None:
    db = await get_db()
    await db.execute(
        "UPDATE skills SET status = 'archived', archived_at = CURRENT_TIMESTAMP "
        "WHERE id = ?",
        (skill_id,)
    )
    await db.commit()


async def restore_skill(skill_id: int) -> None:
    db = await get_db()
    await db.execute(
        "UPDATE skills SET status = 'active', archived_at = NULL WHERE id = ?",
        (skill_id,)
    )
    await db.commit()
async def save_daily_plan_for_skill(user_id: int, skill_id: int, step_type: str) -> None:
    today = datetime.now().strftime("%Y-%m-%d")
    db = await get_db()

    await db.execute(
        "DELETE FROM daily_steps WHERE user_id = ? AND skill_id = ? AND date = ?",
        (user_id, skill_id, today)
    )

    await db.execute(
        "INSERT INTO daily_steps (user_id, skill_id, date, step_type, status) "
        "VALUES (?, ?, ?, ?, 'запланирован')",
        (user_id, skill_id, today, step_type)
    )
    await db.commit()


async def get_all_today_plans(user_id: int) -> list[dict]:
    """Возвращает все планы пользователя на сегодня (по всем навыкам)."""
    today = datetime.now().strftime("%Y-%m-%d")
    db = await get_db()
    async with db.execute(
        "SELECT ds.*, s.name as skill_name FROM daily_steps ds "
        "LEFT JOIN skills s ON ds.skill_id = s.id "
        "WHERE ds.user_id = ? AND ds.date = ? ORDER BY ds.id",
        (user_id, today)
    ) as cursor:
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]
    async def update_step_status_by_skill(user_id: int, skill_id: int, status: str) -> None:
        """Обновляет статус шага по конкретному навыку за сегодня."""
    today = datetime.now().strftime("%Y-%m-%d")
    db = await get_db()
    await db.execute(
        "UPDATE daily_steps SET status = ? "
        "WHERE user_id = ? AND skill_id = ? AND date = ?",
        (status, user_id, skill_id, today)
    )
    await db.commit()