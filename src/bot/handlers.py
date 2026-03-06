import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

logger = logging.getLogger(__name__)

router = Router()


@router.message(Command('help'))
async def cmd_start(message: Message) -> None:
    logger.info('User %s started bot', message.from_user.id)
    await message.answer('default stub')
