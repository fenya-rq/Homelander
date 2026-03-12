import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from src.ai.client import get_response
from src.bot.helpers import parse_data
from src.storage.db import get_or_create_user, get_user_id, save_feed_block

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


# @router.message()
# async def feed_handler(message: Message) -> None:
#     feed_block = await parse_data(message.text, message.date)
#     user_id = await get_user_id(message.from_user.id)
#     await save_feed_block(user_id, feed_block)
#     await message.answer('ok')


# TODO: extend for save to db and return some stats instead `feed_handler` above
@router.message()
async def func_test(message: Message) -> None:
    llm_response = await get_response(message.text)
    await message.answer(f'Ответ от LLM:\n{llm_response}')
