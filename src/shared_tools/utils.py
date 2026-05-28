from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import aiofiles

# from config import FileMarks


async def read_file(
    file_path: Path | str, mode: str, encoding: str | None = 'utf-8'
) -> str | bytes:
    # Binary mode doesn't take an encoding argument
    if 'b' in mode:
        encoding = None

    async with aiofiles.open(file=file_path, mode=mode, encoding=encoding) as file:
        content = await file.read()
    return content


async def write_file(
    content: str | bytes, file_path: Path | str, mode: str, encoding: str | None = 'utf-8'
) -> None:
    # Binary mode doesn't take an encoding argument
    if 'b' in mode:
        encoding = None

    async with aiofiles.open(file=file_path, mode=mode, encoding=encoding) as file:
        await file.write(content)


def get_tz_offset(zone_info: ZoneInfo) -> str:
    """Вспомогательный метод для специфики SQLite."""
    now = datetime.now(zone_info)
    utc_slip = int(now.utcoffset().seconds / 60)
    return f'{utc_slip:+} minutes'
