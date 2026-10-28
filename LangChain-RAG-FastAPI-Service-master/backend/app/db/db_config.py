import os

from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models.chat_history import Base

load_dotenv()

DEFAULT_MYSQL_URL = (
    f"mysql+aiomysql://{os.getenv('MYSQL_USER', 'root')}:{os.getenv('MYSQL_PASSWORD', '')}"
    f"@{os.getenv('MYSQL_HOST', 'localhost')}:{os.getenv('MYSQL_PORT', '3306')}"
    f"/{os.getenv('MYSQL_DATABASE', 'chat_history')}?charset=utf8mb4"
)

ASYNC_DATABSE_URL = os.getenv("DATABASE_URL", DEFAULT_MYSQL_URL)
IS_SQLITE = ASYNC_DATABSE_URL.startswith("sqlite+")

engine_kwargs = {
    "echo": os.getenv("SQL_ECHO", "false").lower() == "true",
}

if IS_SQLITE:
    sqlite_path = ASYNC_DATABSE_URL.split("///", 1)[-1]
    sqlite_dir = os.path.dirname(sqlite_path)
    if sqlite_dir:
        os.makedirs(sqlite_dir, exist_ok=True)
else:
    engine_kwargs.update(
        {
            "pool_size": 10,
            "max_overflow": 20,
        }
    )

async_engine = create_async_engine(ASYNC_DATABSE_URL, **engine_kwargs)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def check_mysql_connection() -> bool:
    try:
        async with async_engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False
