from pathlib import Path

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


#
# def change_filename(filepath: Path) -> None:
#     marked_as_ready = f'{filepath.stem}{FileMarks.PROCESSED}{filepath.suffix}'
#     filepath.rename(Path(filepath.parent, marked_as_ready))