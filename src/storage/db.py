import logging
from datetime import datetime

import aiosqlite

from src.config import DB_PATH, TZ

logger = logging.getLogger(__name__)


async def get_or_create_user(tg_id: int, username: str | None) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
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


async def save_feed_block(user_id: int, values: tuple) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('PRAGMA foreign_keys = ON')

        params = (user_id,) + values
        cursor = await db.execute(
            """
            INSERT INTO feed_data (user_id, energy, meals, created_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT (user_id, date(created_at)) DO UPDATE SET
                energy = energy + excluded.energy,
                meals  = meals || ', ' || excluded.meals
            """,
            params,
        )
        await db.commit()
        logger.debug('Saved record id=%s for user_id=%s', cursor.lastrowid, user_id)
        return cursor.lastrowid
