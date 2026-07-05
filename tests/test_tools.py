import pytest
from app.services.tools import calculate_debt_load, evaluate_rules


# Тесты расчёта долговой нагрузки
def test_calculate_debt_load_basic():
    calc = calculate_debt_load(amount=3_000_000, monthly_income=150_000, term_months=240)
    # платёж должен быть положительным и меньше дохода
    assert calc["monthly_payment"] > 0
    assert calc["debt_load_percent"] > 0
    # при доходе 150к и разумной сумме нагрузка должна быть невысокой (<50%)
    assert calc["debt_load_percent"] < 50


def test_calculate_debt_load_high_burden():
    # огромная сумма при малом доходе = высокая нагрузка
    calc = calculate_debt_load(amount=12_000_000, monthly_income=80_000, term_months=120)
    assert calc["debt_load_percent"] > 50  # нагрузка превышает лимит


# Тесты проверки правил
@pytest.mark.parametrize("amount, income, term, expected_approved", [
    (3_000_000, 150_000, 240, True),    # хорошая заявка → одобрить
    (12_000_000, 80_000, 120, False),   # высокая нагрузка → отклонить
    (20_000_000, 500_000, 240, False),  # сумма > 15 млн → отклонить
    (1_000_000, 100_000, 6, False),     # срок < 12 мес → отклонить
    (11_000_000, 150_000, 240, False),  # >10млн, но доход <200к → отклонить
])
def test_evaluate_rules(amount, income, term, expected_approved):
    calc = calculate_debt_load(amount, income, term)
    verdict = evaluate_rules(amount, income, term, calc)
    assert verdict["approved"] == expected_approved
    assert len(verdict["reasons"]) > 0  # причины всегда есть


def test_evaluate_rules_gives_reasons():
    # отклонённая заявка должна иметь конкретные причины
    calc = calculate_debt_load(20_000_000, 80_000, 120)
    verdict = evaluate_rules(20_000_000, 80_000, 120, calc)
    assert verdict["approved"] is False
    # среди причин должно быть про превышение суммы
    reasons_text = " ".join(verdict["reasons"])
    assert "15 млн" in reasons_text or "превышает" in reasons_text