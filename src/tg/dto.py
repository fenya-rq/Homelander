from dataclasses import dataclass
from datetime import datetime
from typing import Literal
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict


# ===================================================== Dataclasses ====================================================
@dataclass(frozen=True, slots=True)
class BaseNutritionRequest:
    user_id: int
    tz_name: Literal['Europe/Moscow'] = 'Europe/Moscow'

    @property
    def zone_info(self) -> ZoneInfo:
        return ZoneInfo(self.tz_name)


@dataclass(frozen=True, slots=True)
class NutritionStatsRequest(BaseNutritionRequest):
    user_id: int
    days: int = 0
    tz_name: Literal['Europe/Moscow'] = 'Europe/Moscow'

    def __post_init__(self):
        if self.days < 0:
            raise ValueError('Days must be non-negative')


# =================================================== Pydantic Models ==================================================
class ConfiguredBaseModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class User(ConfiguredBaseModel):

    tg_id: int
    name: str


class FeedBase(ConfiguredBaseModel):
    energy: int
    protein: int
    fats: int
    carbohydrates: int
    fiber: int


class FeedNutrients(FeedBase):
    created_at: str


class FeedRequest(FeedNutrients):
    user_id: int


class FeedResponse(FeedNutrients):

    @property
    def human_text(self) -> str:
        date_str = datetime.strptime(self.created_at, '%Y-%m-%d').strftime('%d.%m.%Y')
        return (
            f'📊 **Пищевая ценность:**\n\n'
            f'🔥 Энергия: `{self.energy}` ккал\n'
            f'🍗 Белки: `{self.protein}` г\n'
            f'🥑 Жиры: `{self.fats}` г\n'
            f'🍞 Углеводы: `{self.carbohydrates}` г\n'
            f'🌿 Клетчатка: `{self.fiber}` г\n\n'
            f'🕒 За {date_str} по МСК'
        )
