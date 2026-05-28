import logging
from datetime import datetime

import aiosqlite

from src.shared_tools.utils import get_tz_offset
from src.tg.dto import User, FeedRequest, FeedResponse

logger = logging.getLogger(__name__)


class BaseRepository:
    __slots__ = ('session',)

    def __init__(self, session: aiosqlite.Connection):
        self.session = session


class UserRepository(BaseRepository):
    __slots__ = ('session',)

    async def get_or_create_user(self, user: User) -> int:
        query = """
                INSERT INTO users (tg_id, username, created_at)
                VALUES (?, ?, ?) ON CONFLICT (tg_id) DO
                UPDATE SET username = excluded.username
                RETURNING id
                """

        current_ts = datetime.now()
        params = (user.tg_id, user.name, current_ts)

        async with self.session.execute(query, params) as cursor:
            row = await cursor.fetchone()
            return row[0]

    async def get_user_id(self, tg_id: int) -> int:
        query = 'SELECT id FROM users WHERE tg_id = ?'

        params = (tg_id,)

        async with self.session.execute(query, params) as cursor:
            row = await cursor.fetchone()
            return row[0]


class FeedRepository(BaseRepository):
    __slots__ = ('session',)

    async def save(self, data: FeedRequest) -> int:
        column_names = ', '.join(FeedRequest.model_fields.keys())
        placeholders = ', '.join(['?'] * len(data.model_fields))

        sql = f"""
              INSERT INTO feed_data ({column_names})
              VALUES ({placeholders})
              """
        params = tuple(data.model_dump().values())

        async with self.session.execute(sql, params) as cursor:
            await self.session.commit()
            logger.debug('Saved record id=%s for user_id=%s', cursor.lastrowid, data.user_id)
            return cursor.lastrowid


    async def get_nutrition_stats(self, stat_req: FeedRequest) -> list[FeedResponse]:
        """Получает агрегированную статистику за указанный период."""
        energy, protein, fats, carbohydrates, fiber, created_at = FeedResponse.model_fields.keys()
        tz_slip = get_tz_offset(stat_req.zone_info)

        date_filter = f"'now', '{tz_slip}'"
        if stat_req.days:
            date_filter = f"'now', '{tz_slip}', '-{stat_req.days} days'"

        query = f"""
              SELECT 
                  SUM({energy}) as {energy},
                  SUM({protein}) as {protein},
                  SUM({fats}) as {fats},
                  SUM({carbohydrates}) as {carbohydrates},
                  SUM({fiber}) as {fiber},
                  DATE({created_at}, '{tz_slip}') as {created_at}
              FROM feed_data
              WHERE user_id = {stat_req.user_id}
                AND DATE({created_at}, '{tz_slip}') >= DATE({date_filter})
              GROUP BY {created_at}
              ORDER BY {created_at} ASC
              """

        async with self.session.execute(query) as cursor:
            rows = await cursor.fetchall()

        return [FeedResponse.model_validate(dict(row)) for row in rows]


class RepositoryContainer:
    """Контейнер, который знает о всех репозиториях."""
    __slots__ = ('session', 'user', 'feed',)

    def __init__(self, session):
        self.user = UserRepository(session)
        self.feed = FeedRepository(session)
