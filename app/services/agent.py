import json
import logging

from app.schemas import ApplicationCreate
from app.services.tools import calculate_debt_load, evaluate_rules
from app.services.rag import search_rules
from app.services.llm_client import LLMClient, OllamaClient

log = logging.getLogger("credit_agent")


PROMPT_TEMPLATE = """Ты — кредитный аналитик. Система уже проверила заявку по правилам банка и приняла решение. Твоя задача — написать понятное обоснование этого решения для клиента.

ЗАЯВКА:
- Заявитель: {name}
- Сумма: {amount} руб., доход: {income} руб./мес, срок: {term} мес.
- Ежемесячный платёж: {payment} руб., долговая нагрузка: {debt_load}%

РЕШЕНИЕ СИСТЕМЫ: {verdict}
ПРИЧИНЫ: {reasons}

Напиши краткое вежливое обоснование этого решения на русском (2-3 предложения), опираясь ТОЛЬКО на указанные причины. Не придумывай новых фактов.
Ответь СТРОГО в JSON: {{"reasoning": "текст обоснования"}}"""


async def analyze_application(data: ApplicationCreate, llm: LLMClient | None = None) -> dict:
    """
    Агент: анализирует заявку через цепочку расчёт -> проверка правил -> RAG -> LLM.
    Решение принимает КОД (детерминированно), LLM формулирует обоснование.
    """
    llm = llm or OllamaClient()

    # ШАГ 1: расчёт долговой нагрузки (код, точно)
    calc = calculate_debt_load(data.amount, data.monthly_income, data.term_months)
    log.info(f"Расчёт: платёж={calc['monthly_payment']}, нагрузка={calc['debt_load_percent']}%")

    # ШАГ 2: проверка правил (код — детерминированно!)
    verdict = evaluate_rules(data.amount, data.monthly_income, data.term_months, calc)
    decision = "approved" if verdict["approved"] else "rejected"
    log.info(f"Решение по правилам: {decision}, причины: {verdict['reasons']}")

    # ШАГ 3: RAG — находим релевантные правила (для контекста/наблюдаемости)
    query = f"кредит сумма {data.amount} доход {data.monthly_income} срок {data.term_months} {data.purpose}"
    rules = search_rules(query, top_k=5)
    log.info(f"RAG нашёл правил: {len(rules)}")

    # ШАГ 4: LLM — формулирует обоснование уже принятого решения
    prompt = PROMPT_TEMPLATE.format(
        name=data.applicant_name,
        amount=data.amount,
        income=data.monthly_income,
        term=data.term_months,
        payment=calc["monthly_payment"],
        debt_load=calc["debt_load_percent"],
        verdict="ОДОБРИТЬ" if verdict["approved"] else "ОТКЛОНИТЬ",
        reasons="; ".join(verdict["reasons"]),
    )
    raw = await llm.generate(prompt)
    log.info(f"LLM ответила: {raw[:100]}")

    reasoning = _parse_reasoning(raw, fallback="; ".join(verdict["reasons"]))

    return {
        "decision": decision,                                  # из КОДА
        "confidence": 0.95 if verdict["approved"] else 0.9,
        "reasoning": reasoning,                                # от LLM
    }


def _parse_reasoning(raw: str, fallback: str) -> str:
    """Извлечь reasoning из JSON-ответа LLM, с фолбэком на причины из кода."""
    try:
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start == -1 or end == 0:
            return fallback
        parsed = json.loads(raw[start:end])
        reasoning = parsed.get("reasoning")
        return str(reasoning) if reasoning else fallback
    except (json.JSONDecodeError, ValueError):
        return fallback