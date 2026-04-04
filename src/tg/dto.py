from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Literal
from zoneinfo import ZoneInfo

from pydantic import BaseModel


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

    @property
    def tz_slip(self) -> str:
        now = datetime.now(self.zone_info)
        utc_slip = int(now.utcoffset().seconds / 60)
        return f'{utc_slip:+} minutes'


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
            f'🕒 {self.created_at.strftime('%d.%m.%Y')}'
        )
