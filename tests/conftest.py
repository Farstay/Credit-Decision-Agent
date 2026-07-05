import pytest
import pytest_asyncio
from unittest.mock import AsyncMock
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
import atexit

from app.main import app
from app.database import get_db, Base
import app.api.applications as applications_module


# --- Тестовый движок: SQLite в памяти ---
test_engine = create_async_engine("sqlite+aiosqlite:///:memory:")
TestSession = async_sessionmaker(test_engine, expire_on_commit=False)


@pytest_asyncio.fixture
async def db_setup():
    """Создаём таблицы в тестовой БД перед тестом, удаляем после."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client(db_setup):
    """HTTP-клиент к приложению с подменённой БД."""
    # подменяем get_db на тестовую сессию
    async def override_get_db():
        async with TestSession() as session:
            yield session
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()  # очистка после теста


@pytest.fixture
def mock_agent(monkeypatch):
    """Мокаем агента, чтобы e2e не гонял реальную LLM."""
    async def fake_analyze(data, llm=None):
        return {"decision": "approved", "confidence": 0.95, "reasoning": "Тестовое решение"}
    monkeypatch.setattr(applications_module, "analyze_application", fake_analyze)

def _dispose_engine():
    import asyncio
    try:
        asyncio.run(test_engine.dispose())
    except Exception:
        pass

atexit.register(_dispose_engine)