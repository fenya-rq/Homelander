import json
import re
from datetime import datetime

from src.config import TZ


class ParserError(Exception):
    pass


# todo: refactor to handle dates
# async def parse_data(user_data: str, msg_date: datetime):
#     lines = [line.strip() for line in user_data.strip().split('\n')]
#
#     try:
#         kkal = int(lines[0])
#     except (ValueError, IndexError):
#         raise ParserError('Первая строка должна быть числом калорий!')
#
#     text = lines[1] if len(lines) > 1 else None
#
#     date = msg_date
#     if len(lines) > 2:
#         try:
#             day, month = lines[2].split('.')
#             date = datetime(day=int(day), month=int(month), year=msg_date.year)
#         except (ValueError, AttributeError):
#             raise ParserError('Введите дату в формате "день.месяц", например: 10.03')
#
#     return kkal, text, date.astimezone(tz=TZ)


def _extract_balanced_json(text: str) -> str | None:
    start = text.find('{')
    if start == -1:
        return None

    depth = 0
    for i, ch in enumerate(text[start:], start=start):
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1

            if depth == 0:
                return text[start:i + 1]

    return None


def clean_and_parse_json(text: str) -> dict | None:
    if text.startswith('{') and text.endswith('}'):
        return json.loads(text)

    code_match = re.search(r'```(?:json)?\s*(.*?)```', text, re.DOTALL)

    if code_match:
        text = code_match.group(1)

    json_str = _extract_balanced_json(text)

    if not json_str:
        return None

    return json.loads(json_str.strip())
