import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from src.ai.client import aclient
from src.bot.conf import settings
from src.bot import handlers
from src.storage.runner import migrate

logger = logging.getLogger(__name__)

bot = Bot(
    token=settings.BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)

dp = Dispatcher()
dp.include_router(handlers.router)  # stub


async def on_shutdown(dispatcher: Dispatcher):
    logger.info('Закрываю соединение с Gemini API...')
    await aclient.aclose()


dp.shutdown.register(on_shutdown)


async def main() -> None:
    logger.info('Start migration...')
    # todo: make manage migrations via cli flag
    await migrate()

    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
