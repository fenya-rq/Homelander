import json
import logging
from datetime import datetime

from pydantic import BaseModel

from src.config import TZ
from src.bot.helpers import clean_and_parse_json
from src.storage.db import save_feed_block

logger = logging.getLogger(__name__)


class FeedDTO(BaseModel):
    energy: int
    protein: int
    fats: int
    carbohydrates: int
    fiber: int
    user_id: int | None = None
    created_at: datetime | None = None

    @property
    def human_text(self) -> str:
        return (
            f'📊 **Пищевая ценность:**\n\n'
            f'🔥 Энергия: `{self.energy}` ккал\n'
            f'🍗 Белки: `{self.protein}` г\n'
            f'🥑 Жиры: `{self.fats}` г\n'
            f'🍞 Углеводы: `{self.carbohydrates}` г\n'
            f'🌿 Клетчатка: `{self.fiber}` г\n\n'
            f'🕒 {self.created_at.strftime('%d.%m.%Y %H:%M')}'
        )


class FeedDataManager:

    def __init__(self, data: str) -> None:
        self.data = data
        self.json_data: FeedDTO | None = None

    def validate_and_assign_data(self) -> bool:
        try:
            if json_data := clean_and_parse_json(self.data):
                self.json_data = FeedDTO(**json_data)
                self.json_data.created_at = datetime.now(tz=TZ)
                return True
        except Exception as e:
            logger.error(e)

        return False

    async def save_feed_block(self, user_id: int) -> FeedDTO | None:
        if not self.validate_and_assign_data():
            return None
        self.json_data.user_id = user_id
        await save_feed_block(self.json_data.model_dump())
        return self.json_data
