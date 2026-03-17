import logging

from aiogram.types import BufferedInputFile

from src.shared_tools.constants import AIError
from src.bot.dto import FeedDTO
from src.bot.helpers import clean_and_parse_json, generate_weekly_chart
from src.storage.db import get_nutrition_stats, save_feed_block

logger = logging.getLogger(__name__)


class FeedDataManager:

    def _parse_to_dto(self, data: str, date_) -> FeedDTO:
        """Преобразует текстовый ответ LLM в валидированный объект DTO.

        Args:
            data: JSON-строка или текст с разметкой от модели.
            date_: Дата и время создания записи.

        Returns:
            Объект FeedDTO с установленной датой.

        Raises:
            AIError: Если не удалось извлечь или распарсить JSON.
        """
        json_dict = clean_and_parse_json(data)
        if not json_dict:
            raise AIError("Can't parse LLM response as JSON")

        dto = FeedDTO(**json_dict)
        dto.created_at = date_
        return dto

    async def process_and_save(self, user_id: int, raw_data: str, msg_date) -> FeedDTO:
        """Обрабатывает сырые данные от LLM и сохраняет их в базу данных.

        Args:
            user_id: Телеграм-идентификатор пользователя.
            raw_data: Ответ от Gemini API.
            msg_date: Дата получения сообщения.

        Returns:
            Созданный и сохраненный объект FeedDTO.
        """
        dto = self._parse_to_dto(raw_data, msg_date)

        payload = dto.model_dump()
        payload['user_id'] = user_id

        await save_feed_block(payload)
        return dto

    async def get_today_stats(self, user_id: int) -> FeedDTO | None:
        """Получает агрегированную статистику питания за текущие сутки.

        Args:
            user_id: Идентификатор пользователя.

        Returns:
           Объект FeedDTO с итогами дня или None, если данных нет.
        """
        stats = await get_nutrition_stats(user_id)
        return stats[0] if stats else None

    async def get_weekly_stats(self, user_id: int) -> BufferedInputFile:
        """Формирует графический отчет по калориям за последние 7 дней.

        Args:
            user_id: Идентификатор пользователя.

        Returns:
            Файл с графиком, готовый для отправки через Telegram API.
        """
        stats = await get_nutrition_stats(user_id, 6)
        return generate_weekly_chart(stats)

feed_manager = FeedDataManager()
