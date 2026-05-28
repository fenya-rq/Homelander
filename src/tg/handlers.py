import logging
from datetime import datetime

from aiogram import Bot, Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove

from src.ai.client import ALT_LLM, MAIN_LLM, ElevenLabsClient, GeminiClient, nutritionist_gemini_config
from src.storage.repositories import RepositoryContainer
from src.tg.dto import FeedRequest
from src.tg.keyboards import get_week_dates_keyboard, DateCallback, CancelCallback
from src.tg.managers import UserManager, FeedDataManager
from src.shared_tools.constants import BaseDomainError

logger = logging.getLogger(__name__)

router = Router()

elevenlabs_client = ElevenLabsClient()

gemini_client = GeminiClient(MAIN_LLM, (ALT_LLM,), nutritionist_gemini_config)


# user_manager = UserManager()
# feed_manager = FeedDataManager()

class FoodLog(StatesGroup):
    waiting_for_date = State()
    waiting_for_food = State()


@router.message(Command('cancel'))
@router.message(F.text.casefold() == 'отмена')
async def cmd_cancel(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return await message.answer('Нечего отменять 🤷‍♂️')

    await state.clear()
    await message.answer(
        'Действие отменено ❌',
        reply_markup=ReplyKeyboardRemove()
    )


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
async def cmd_create_user(message: Message, repos: RepositoryContainer) -> None:
    user_id, username = message.from_user.id, message.from_user.username
    await repos.user.get_or_create_user(user_id, username)
    await message.answer(f'User {username} has created!')


@router.message(Command('daystats'))
async def get_day_stats(message: Message, repos: RepositoryContainer):
    user_id = await repos.user.get_user_id(message.from_user.id)
    stats = await FeedDataManager(repos=repos).get_today_stats(user_id)
    if stats is None:
        return await message.answer('За сегодня записей еще нет. Пора что-нибудь съесть! 🍽')
    return await message.answer(f'📅 **Статистика за сегодня:**\n\n{stats.human_text}', parse_mode='Markdown')


@router.message(Command('weekstats'))
async def get_week_stats(message: Message, repos: RepositoryContainer):
    user_id = await repos.user.get_user_id(message.from_user.id)
    stats_chart = await FeedDataManager(repos=repos).get_weekly_stats(user_id)
    await message.answer_photo(photo=stats_chart, caption='📊 Твой прогресс питания за неделю')


@router.message(Command('add_past'))
async def start_past_log(message: Message, state: FSMContext):
    await message.answer(
        'Выберите дату из списка ниже, чтобы добавить запись о приеме пищи за прошлые дни.\n\n',
        reply_markup=get_week_dates_keyboard()
    )
    await state.set_state(FoodLog.waiting_for_date)


@router.callback_query(CancelCallback.filter())
async def cancel_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text('Запись отменена ↩️')
    await callback.answer()


@router.callback_query(DateCallback.filter(), FoodLog.waiting_for_date)
async def process_date_callback(callback: CallbackQuery, callback_data: DateCallback, state: FSMContext):
    chosen_date = callback_data.date_str

    await state.update_data(chosen_date=chosen_date)
    await callback.message.edit_text(f'📅 Выбрана дата: <b>{chosen_date}</b>\n🥗 Что вы ели?\n')
    await state.set_state(FoodLog.waiting_for_food)

    await callback.answer()


async def process_text_logic(message: Message, text: str, repos: RepositoryContainer, override_date=None):
    """Общая логика обработки текста, очищенная от специфики хэндлеров."""
    msg_date = override_date or message.date
    user_id = await repos.user.get_user_id(message.from_user.id)
    err_msg = 'Произошла системная ошибка при сохранении данных.'

    try:
        raw_response = await gemini_client.get_response(text)
        if raw_response is None:
            return await message.answer('Внутренняя ошибка AI агента, попробуйте еще раз.')

        try:
            nutrients = await gemini_client.parse_to_dto(raw_response, msg_date)

            feed_record = FeedRequest(**nutrients.model_dump(), user_id=user_id)

            await FeedDataManager(repos=repos).process_and_save(feed_record)

            return await message.answer(f'{nutrients.human_text}', parse_mode='Markdown')

        except BaseDomainError as e:
            logger.error(e)
            return await message.answer(f'Уточнение от агента:\n{raw_response}')

        except Exception:
            logger.exception('Unexpected error for user %s', user_id)
            return await message.answer(err_msg)

    except Exception as e:
        logger.error('AI Client error for user %s, error:\n%s', user_id, e)
        await message.answer(err_msg)


@router.message(F.voice)
async def feed_prompt_handler_voice(message: Message, bot: Bot, state: FSMContext, repos: RepositoryContainer):
    file = await bot.get_file(message.voice.file_id)
    downloaded = await bot.download_file(file.file_path)

    override_date = None
    data = await state.get_data()
    if chosen_date_str := data.get('chosen_date'):
        override_date = datetime.fromisoformat(chosen_date_str)
        await state.clear()

    text = await elevenlabs_client.speech_to_text(downloaded.read())
    if not text:
        return await message.answer('Не удалось распознать речь.')

    logger.debug('Text phrase: %s', text.text)
    await process_text_logic(message, text, repos, override_date)


@router.message()
async def feed_prompt_handler(message: Message, repos: RepositoryContainer):
    if not message.text:
        return
    await process_text_logic(message, message.text, repos)
