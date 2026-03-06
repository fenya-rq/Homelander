import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from src.bot.config import settings
from src.bot import handlers
from src.bot import db

logger = logging.getLogger(__name__)

bot = Bot(
    token=settings.BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN_V2),
)

dp = Dispatcher()
dp.include_router(handlers.router)  # stub





async def main() -> None:
    await db.init_db()  # stub
    await dp.start_polling(bot)

    logger.info('Bot started')


if __name__ == "__main__":
    asyncio.run(main())