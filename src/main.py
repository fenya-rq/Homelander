import asyncio
import logging

from src.tg.bot import bot as tg_bot, dp as tg_dp
from src.storage.runner import migrate

logger = logging.getLogger(__name__)


async def main() -> None:
    logger.info('Start migration...')
    # todo: make manage migrations via cli flag
    await migrate()

    await tg_dp.start_polling(tg_bot)


if __name__ == '__main__':
    asyncio.run(main())