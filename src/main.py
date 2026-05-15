import asyncio
import logging

from src.tg.bot import bot as tg_bot, dp as tg_dp
from src.tg.middlewares import DbSessionMiddleware
from src.storage.db import get_session_pool

logger = logging.getLogger('src.main')


async def main() -> None:
    session_pool = await get_session_pool()
    tg_dp.update.outer_middleware(DbSessionMiddleware(session_pool))

    try:
        await tg_dp.start_polling(tg_bot)
    finally:
        await session_pool.close()


if __name__ == '__main__':
    asyncio.run(main())
