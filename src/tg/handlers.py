import logging

from aiogram import Bot, Router, F
from aiogram.filters import Command
from aiogram.types import Message

from src.ai.client import elevenlabs_client, get_response
from src.tg.managers import FeedDTO, feed_manager
from src.shared_tools.constants import BaseDomainError
from src.storage.db import get_or_create_user, get_user_id

logger = logging.getLogger(__name__)

router = Router()


@router.message(Command('help'))
async def cmd_start(message: Message) -> None:
    await message.answer(
        'Шаблон для записи твоих данных:\n'
        '1. ККал (сколько калорий было потреблено)\n'
        '2. Еда (просто перечисли через запятую, что ты ел)\n'
        '3. Дата в формате "день.месяц", например: 10.03'
        ' (если не укажешь, будет записано в текущий день)\n\n'
        'Пример:\n'
        '2500\n'
        'пицца, кола\n'
        '10.03\n\n'
        'Получить последние записи за текущий день - /day\n'
        'Получить последние записи за предыдущий день - /yesterday'
    )


@router.message(Command('createuser'))
async def cmd_create_user(message: Message) -> None:
    user_id, username = message.from_user.id, message.from_user.username
    await get_or_create_user(user_id, username)
    await message.answer(f'User {username} has created!')


@router.message(Command('daystats'))
async def get_day_stats(message: Message):
    user_id = await get_user_id(message.from_user.id)
    stats = await feed_manager.get_today_stats(user_id)
    if stats is None:
        return await message.answer('За сегодня записей еще нет. Пора что-нибудь съесть! 🍽')
    return await message.answer(f'📅 **Статистика за сегодня:**\n\n{stats.human_text}', parse_mode='Markdown')


@router.message(Command('weekstats'))
async def get_week_stats(message: Message):
    user_id = await get_user_id(message.from_user.id)
    stats_chart = await feed_manager.get_weekly_stats(user_id)
    await message.answer_photo(photo=stats_chart, caption='📊 Твой прогресс питания за неделю')


# TODO: finish the handler
@router.message(F.voice)
async def voice(message: Message, bot: Bot):
    file = await bot.get_file(message.voice.file_id)
    downloaded = await bot.download_file(file.file_path)
    text = await elevenlabs_client.speech_to_text(downloaded.read())
    print(f'result: {text}')
    print(f'result type: {type(text)}')


@router.message()
async def feed_prompt_handler(message: Message):
    """This is a greedy handler - he catches all any text messages.

    Therefore, we need to place it to end of handlers order.
    """
    msg_date = message.date
    user_id = await get_user_id(message.from_user.id)

    try:
        llm_response = await get_response(message.text)
        if llm_response is None:
            return await message.answer(f'Внутренняя ошибка AI агента, попробуйте еще раз.')

        try:
            saved_dto: FeedDTO = await feed_manager.process_and_save(user_id, llm_response, msg_date)
            return await message.answer(f'{saved_dto.human_text}', parse_mode='Markdown')

        except BaseDomainError as e:
            logger.error(e)
            return await message.answer(f'Уточнение от агента:\n{llm_response}')

        except Exception as e:
            logger.exception('Unexpected error for user %s', user_id)
            return await message.answer('Произошла системная ошибка при сохранении данных.')

    except Exception as e:
        logger.error('AI Client error for user %s, error:\n%s', (user_id, e))
        return await message.answer('Произошла системная ошибка при сохранении данных.')
