import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from src.ai.client import gemini_client
from src.storage.runner import migrate
from src.tg.conf import settings
from src.tg import handlers

logger = logging.getLogger(__name__)

bot = Bot(
    token=settings.BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)

dp = Dispatcher()
dp.include_router(handlers.router)  # stub


async def on_start(dispatcher: Dispatcher):
    logger.info('Bot started!')
    # todo: make manage migrations via cli flag
    logger.info('Start migration...')
    await migrate()


async def on_shutdown(dispatcher: Dispatcher):
    logger.info('Закрываю соединение с Gemini API...')
    await gemini_client.aclose()


dp.startup.register(on_start)
dp.shutdown.register(on_shutdown)
