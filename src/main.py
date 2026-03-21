import asyncio
import logging

from src.tg.bot import bot as tg_bot, dp as tg_dp

logger = logging.getLogger('src.main')


async def main() -> None:
    await tg_dp.start_polling(tg_bot)


if __name__ == '__main__':
    asyncio.run(main())