from datetime import datetime

from src.config import TZ


class ParserError(Exception):
    pass


async def parse_data(user_data: str, msg_date: datetime):
    lines = [line.strip() for line in user_data.strip().split('\n')]

    try:
        kkal = int(lines[0])
    except (ValueError, IndexError):
        raise ParserError('Первая строка должна быть числом калорий!')

    text = lines[1] if len(lines) > 1 else None

    date = msg_date
    if len(lines) > 2:
        try:
            day, month = lines[2].split('.')
            date = datetime(day=int(day), month=int(month), year=msg_date.year)
        except (ValueError, AttributeError):
            raise ParserError('Введите дату в формате "день.месяц", например: 10.03')

    return kkal, text, date.astimezone(tz=TZ)
