import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from src.bot.config import settings
from src.bot import handlers

logger = logging.getLogger(__name__)

bot = Bot(
    token=settings.BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)

dp = Dispatcher()
dp.include_router(handlers.router)  # stub



async def main() -> None:
    logger.info('Bot started')
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())