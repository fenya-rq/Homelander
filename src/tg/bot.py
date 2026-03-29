import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from src.config import BOT_ADMIN_ID
from src.storage.runner import migrate
from src.tg.conf import settings
from src.tg.handlers import elevenlabs_client, gemini_client
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


# todo: find correct way to close Gemini client connection, since it uses aiohttp under the hood, we can just close the session, but we need to add this method to our GeminiClient class first.
# async def on_shutdown(dispatcher: Dispatcher):
#     logger.info('Закрываю соединение с Gemini API...')
#     await gemini_client.aclose()


# todo: test it before commit
async def notify_admin_about_11labs_limits(remains):
    await bot.send_message(BOT_ADMIN_ID, f'⚠️ Внимание! Лимиты ElevenLabs на исходе: {remains} симв.')


elevenlabs_client.set_low_limit_handler(notify_admin_about_11labs_limits)

# STUB for Gemini limits notification, since we have no method to get remaining limits from Gemini API, we just will notify admin when we catch 429 error for all models.
async def notify_admin_about_google_limits():
    await bot.send_message(BOT_ADMIN_ID, f'⚠️ Внимание! Лимиты Gemini для всех Free-Tier моделей исчерпаны.')


gemini_client.set_low_limit_handler(notify_admin_about_google_limits)

dp.startup.register(on_start)
# dp.shutdown.register(on_shutdown)
