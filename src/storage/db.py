import logging
from asyncio import Queue
from datetime import datetime

import aiosqlite

from src.config import DB_PATH

logger = logging.getLogger(__name__)


class AioSqlitePool:
    def __init__(self, db_path: str, max_connections: int = 5):
        self.db_path = db_path
        self.max_connections = max_connections
        self._pool: Queue[aiosqlite.Connection] = Queue()

    async def init(self) -> None:
        """Заполняем пул настроенными соединениями."""
        for _ in range(self.max_connections):
            conn = await aiosqlite.connect(self.db_path)
            conn.row_factory = aiosqlite.Row

            # Настраиваем один раз при старте приложения
            await conn.execute('PRAGMA journal_mode = WAL')
            await conn.execute('PRAGMA synchronous = NORMAL')
            await conn.execute('PRAGMA cache_size = 10000')
            await conn.execute('PRAGMA temp_store = MEMORY')
            await conn.execute('PRAGMA foreign_keys = ON')
            await conn.execute('PRAGMA mmap_size = 268435456')

            self._pool.put_nowait(conn)

    def acquire(self):
        """Контекстный менеджер для взятия коннекта из пула."""
        return _ConnectionContextManager(self._pool)

    async def close(self) -> None:
        """Закрываем все соединения при остановке бота."""
        while not self._pool.empty():
            conn = await self._pool.get()
            await conn.close()


class _ConnectionContextManager:
    def __init__(self, pool_queue: Queue):
        self.pool_queue = pool_queue
        self.conn = None

    async def __aenter__(self) -> aiosqlite.Connection:
        self.conn = await self.pool_queue.get()
        return self.conn

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if self.conn:
            self.pool_queue.put_nowait(self.conn)


async def get_session_pool(db_path: str = DB_PATH) -> AioSqlitePool:
    """Фабрика для создания и инициализации пула соединений."""
    pool = AioSqlitePool(db_path, max_connections=10)
    await pool.init()  # Здесь один раз выполняются все PRAGMA для каждого соединения
    return pool

# async def get_connection(db_path: str = DB_PATH) -> aiosqlite.Connection:
#     conn = await aiosqlite.connect(db_path)
#     conn.row_factory = aiosqlite.Row
#
#     await conn.execute("PRAGMA journal_mode = WAL")
#     await conn.execute("PRAGMA synchronous = NORMAL")
#     await conn.execute("PRAGMA cache_size = 10000")
#     await conn.execute("PRAGMA temp_store = MEMORY")
#     await conn.execute("PRAGMA foreign_keys = ON")
#     await conn.execute("PRAGMA mmap_size = 268435456")
#
#     return conn
#

# todo: refactor this module, take out sql queries to separate managers (like FeedDataManager) and make this module responsible only for low-level db operations
#  (like connection management, transactions, etc.). Also, we can use connection pool for better performance, since aiosqlite supports it via aiosqlite.Pool.
async def save_migration_file(name: str) -> None:
    """Сохраняет информацию о выполненной миграции в базу данных."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('PRAGMA journal_mode=WAL;')
        await db.execute('PRAGMA foreign_keys = ON')

        current_ts = datetime.now()
        await db.execute(
            'INSERT OR IGNORE INTO migrations (filename, applied_at) VALUES (?, ?)',
            (name, current_ts),
        )
        await db.commit()
        logger.debug('Saved migration %s at %s', name, current_ts)
