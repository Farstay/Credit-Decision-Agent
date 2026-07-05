import pytest
from unittest.mock import AsyncMock
from app.schemas import ApplicationCreate
from app.services.agent import analyze_application
from app.services.llm_client import LLMClient
import app.services.agent as agent_module


@pytest.fixture(autouse=True)
def mock_rag(monkeypatch):
    """Мокаем RAG-поиск, чтобы тесты не ходили в реальный Qdrant."""
    def fake_search(query, top_k=5):
        return ["Правило 1: тестовое", "Правило 2: тестовое"]
    monkeypatch.setattr(agent_module, "search_rules", fake_search)


@pytest.fixture
def good_application():
    return ApplicationCreate(
        applicant_name="Иван Петров",
        amount=3_000_000, monthly_income=150_000,
        purpose="Ипотека", term_months=240,
    )


@pytest.fixture
def bad_application():
    return ApplicationCreate(
        applicant_name="Пётр Сидоров",
        amount=12_000_000, monthly_income=80_000,
        purpose="Ипотека", term_months=120,
    )


async def test_agent_approves_good_application(good_application):
    fake_llm = AsyncMock(spec=LLMClient)
    fake_llm.generate.return_value = '{"reasoning": "Все требования выполнены"}'
    result = await analyze_application(good_application, llm=fake_llm)
    assert result["decision"] == "approved"
    assert result["confidence"] == 0.95
    fake_llm.generate.assert_called_once()


async def test_agent_rejects_bad_application(bad_application):
    fake_llm = AsyncMock(spec=LLMClient)
    fake_llm.generate.return_value = '{"reasoning": "Долговая нагрузка превышена"}'
    result = await analyze_application(bad_application, llm=fake_llm)
    assert result["decision"] == "rejected"
    assert result["confidence"] == 0.9


async def test_agent_handles_broken_llm_response(good_application):
    fake_llm = AsyncMock(spec=LLMClient)
    fake_llm.generate.return_value = "это не JSON вообще"
    result = await analyze_application(good_application, llm=fake_llm)
    assert result["decision"] == "approved"
    assert len(result["reasoning"]) > 0