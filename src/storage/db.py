import logging
from datetime import datetime

import aiosqlite

from src.config import DB_PATH, TZ
from src.tg.dto import FeedDTO, NutritionStatsRequest

logger = logging.getLogger(__name__)


async def save_migration_file(name: str) -> None:
    """Сохраняет информацию о выполненной миграции в базу данных."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('PRAGMA journal_mode=WAL;')
        await db.execute('PRAGMA foreign_keys = ON')

        current_ts = datetime.now(tz=TZ)
        await db.execute(
            'INSERT OR IGNORE INTO migrations (filename, applied_at) VALUES (?, ?)',
            (name, current_ts),
        )
        await db.commit()
        logger.debug('Saved migration %s at %s', name, current_ts)


async def get_or_create_user(tg_id: int, username: str | None) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('PRAGMA journal_mode=WAL;')
        await db.execute('PRAGMA foreign_keys = ON')

        current_ts = datetime.now(tz=TZ)
        async with db.execute(
            """
            INSERT INTO users (tg_id, username, created_at)
            VALUES (?, ?, ?)
            ON CONFLICT (tg_id) DO UPDATE SET username = excluded.username
            RETURNING id
            """,
            (tg_id, username, current_ts),
        ) as cursor:
            row = await cursor.fetchone()
            await db.commit()
            return row[0]


async def get_user_id(tg_id: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('PRAGMA foreign_keys = ON')
        async with db.execute(
            'SELECT id FROM users WHERE tg_id = ?', (tg_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return row[0]


async def save_feed_block(data: FeedDTO) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('PRAGMA journal_mode=WAL;')
        await db.execute('PRAGMA foreign_keys = ON;')

        sql = """
              INSERT INTO feed_data (user_id, energy, protein, fats, carbohydrates, fiber, created_at)
              VALUES (?, ?, ?, ?, ?, ?, ?) 
              """
        row_to_save = (
            data['user_id'], data['energy'], data['protein'],
            data['fats'], data['carbohydrates'], data['fiber'], data['created_at']
        )

        cursor = await db.execute(sql, row_to_save)
        await db.commit()
        logger.debug('Saved record id=%s for user_id=%s', cursor.lastrowid, data['user_id'])
        return cursor.lastrowid


async def get_nutrition_stats(stat_req: NutritionStatsRequest) -> list[FeedDTO]:
    """Получает агрегированную статистику за указанный период."""
    # Если days=0, берем только сегодня, если > 0, то интервал
    date_filter = f"'now', '{stat_req.tz_slip}'"
    if stat_req.days > 0:
        date_filter = f"{date_filter}, '-{stat_req.days} days'"

    sql = f"""
          SELECT 
              SUM(energy),
              SUM(protein),
              SUM(fats),
              SUM(carbohydrates),
              SUM(fiber),
              DATE(created_at, '{stat_req.tz_slip}') as day
          FROM feed_data
          WHERE user_id = ?
            AND DATE(created_at, '{stat_req.tz_slip}') >= DATE({date_filter})
          GROUP BY day
          ORDER BY day ASC
          """

    async with aiosqlite.connect(DB_PATH) as db:

        async with db.execute(sql, (stat_req.user_id,)) as cursor:
            rows = await cursor.fetchall()

            return [
                FeedDTO(
                    energy=row[0],
                    protein=row[1],
                    fats=row[2],
                    carbohydrates=row[3],
                    fiber=row[4],
                    created_at=datetime.strptime(row[5], '%Y-%m-%d') if stat_req.days else datetime.now(stat_req.zone_info).date()
                )
                for row in rows if row[0] is not None
            ]
