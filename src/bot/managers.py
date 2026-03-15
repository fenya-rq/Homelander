import logging
from datetime import datetime

from src.config import TZ
from src.shared_tools.constants import AIError
from src.bot.dto import FeedDTO
from src.bot.helpers import clean_and_parse_json
from src.storage.db import get_today_stats, get_user_id, save_feed_block

logger = logging.getLogger(__name__)


class FeedDataManager:

    def _parse_to_dto(self, data: str, date_) -> FeedDTO:
        json_dict = clean_and_parse_json(data)
        if not json_dict:
            raise AIError("Can't parse LLM response as JSON")

        dto = FeedDTO(**json_dict)
        dto.created_at = date_
        return dto

    async def process_and_save(self, user_id: int, raw_data: str, msg_date) -> FeedDTO:
        dto = self._parse_to_dto(raw_data, msg_date)

        payload = dto.model_dump()
        payload['user_id'] = user_id

        await save_feed_block(payload)
        return dto

    async def get_today_stats(self, user_id: int) -> FeedDTO | None:
        return await get_today_stats(user_id)


feed_manager = FeedDataManager()
