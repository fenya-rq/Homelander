import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from src.ai.client import get_response
from src.bot.managers import FeedDataManager, FeedDTO
from src.storage.db import get_or_create_user, get_user_id

logger = logging.getLogger(__name__)

router = Router()


@router.message(Command('createuser'))
async def cmd_create_user(message: Message) -> None:
    user_id, username = message.from_user.id, message.from_user.username
    await get_or_create_user(user_id, username)
    await message.answer(f'User {username} has created!')


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


@router.message(Command('day'))
async def day_report(message: Message) -> None:
    await message.answer('stub for /day')


@router.message(Command('yesterday'))
async def yesterday_report(message: Message) -> None:
    await message.answer('stub for /day')


@router.message()
async def func_test(message: Message):
    llm_response = await get_response(message.text)
    if llm_response is None:
        await message.answer(f'Внутренняя ошибка AI агента, попробуйте еще раз.')

    user_id = await get_user_id(message.from_user.id)
    feed_manager = FeedDataManager(llm_response)

    saved_dto: FeedDTO = await feed_manager.save_feed_block(user_id)
    # todo: refactor Manager class to singleton and after this handler
    if not saved_dto:
        await message.answer(f'Ответ не был записан в БД, попробуйте еще раз!\n{llm_response}')

    await message.answer(f'{saved_dto.human_text}', parse_mode='Markdown')
