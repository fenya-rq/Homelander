import logging
from datetime import datetime

import aiosqlite

from src.config import DB_PATH, TZ

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


async def save_feed_block(data) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('PRAGMA journal_mode=WAL;')
        await db.execute('PRAGMA foreign_keys = ON;')

        cursor = await db.execute(
            """
            INSERT INTO feed_data (user_id, energy, protein, fats, carbohydrates, fiber, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?) 
            ON CONFLICT(user_id, date(created_at)) 
            DO UPDATE SET
                energy = energy + excluded.energy,
                protein = protein + excluded.protein,
                fats = fats + excluded.fats,
                carbohydrates = carbohydrates + excluded.carbohydrates,
                fiber = fiber + excluded.fiber
            """,
            (
                data['user_id'], data['energy'], data['protein'],
                data['fats'], data['carbohydrates'], data['fiber'], data['created_at']
            ),
        )
        await db.commit()
        logger.debug('Saved record id=%s for user_id=%s', cursor.lastrowid, data['user_id'])
        return cursor.lastrowid
