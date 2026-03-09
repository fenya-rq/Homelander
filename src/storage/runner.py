from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import aiosqlite

from src.config import BASE_DIR, DB_PATH


async def migrate() -> None:
    _migration_path = BASE_DIR / 'bot' / 'migrations'
    for path in sorted(Path(_migration_path).glob('[0-9]*.py')):
        spec = spec_from_file_location('migration', path)
        module = module_from_spec(spec)
        spec.loader.exec_module(module)

        async with aiosqlite.connect(DB_PATH) as db:
            await db.executescript(module.ddl)
            await db.commit()
