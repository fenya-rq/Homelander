from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import aiosqlite

from src.config import BASE_DIR, DB_PATH
from src.storage.db import save_migration_file


async def migrate() -> None:
    _migration_path = BASE_DIR / 'bot' / 'migrations'
    for path in sorted(Path(_migration_path).glob('[0-9]*.py')):
        spec = spec_from_file_location('migration', path)
        module = module_from_spec(spec)
        spec.loader.exec_module(module)

        migration_name = module.__file__.rsplit('/', 1)[-1]

        async with aiosqlite.connect(DB_PATH) as db:
            await db.executescript(module.ddl)
            await save_migration_file(migration_name)
            await db.commit()
