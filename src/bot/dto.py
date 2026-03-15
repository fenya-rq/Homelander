from datetime import datetime

from pydantic import BaseModel


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
