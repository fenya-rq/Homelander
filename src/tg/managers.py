import logging

from aiogram.types import BufferedInputFile

from src.shared_tools.interfaces import BaseManagerInterface
from src.tg.dto import NutritionStatsRequest, FeedResponse, FeedRequest, User
from src.tg.helpers import generate_weekly_chart

logger = logging.getLogger(__name__)


class UserManager(BaseManagerInterface):


    async def get_or_create_user(self, user: User):
        return await self.repos.user.get_or_create_user(user)

    async def get_user_id(self, tg_id: int) -> int:
        return await self.repos.user.get_user_id(tg_id)


class FeedDataManager(BaseManagerInterface):

    async def process_and_save(self, feed_record: FeedRequest) -> FeedResponse:
        """Обрабатывает сырые данные от LLM и сохраняет их в базу данных.

        Args:
            feed_record: ...
        Returns:
            Созданный и сохраненный объект FeedDTO.
        """
        await self.repos.feed.save(feed_record)
        return FeedResponse(**feed_record.model_dump())

    async def get_today_stats(self, stat_req: NutritionStatsRequest) -> FeedResponse | None:
        """Получает агрегированную статистику питания за текущие сутки.

        Args:
            stat_req: ...

        Returns:
           Объект FeedDTO с итогами дня или None, если данных нет.
        """
        stats = self.repos.feed.get_nutrition_stats(stat_req)
        return stats[0] if stats else None

    async def get_weekly_stats(self, stat_req: NutritionStatsRequest) -> BufferedInputFile:
        """Формирует графический отчет по калориям за последние 7 дней.

        Args:
            stat_req: ...

        Returns:
            Файл с графиком, готовый для отправки через Telegram API.
        """
        stats = self.repos.feed.get_nutrition_stats(stat_req)
        return generate_weekly_chart(stats)
