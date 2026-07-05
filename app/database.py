from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


class Base(DeclarativeBase):
    pass


# async-движок с пулом соединений
engine = create_async_engine(
    settings.database_url,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    echo=False,
)

# фабрика async-сессий
async_session_maker = async_sessionmaker(
    engine,
    expire_on_commit=False,
)

# зависимость для FastAPI
async def get_db():
    async with async_session_maker() as session:
        yield session