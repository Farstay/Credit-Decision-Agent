def calculate_debt_load(amount: float, monthly_income: float, term_months: int,
                        annual_rate: float = 0.08) -> dict:
    """
    Инструмент: расчёт ежемесячного аннуитетного платежа и долговой нагрузки.
    """
    monthly_rate = annual_rate / 12
    if monthly_rate > 0:
        payment = amount * (monthly_rate * (1 + monthly_rate) ** term_months) / \
                  ((1 + monthly_rate) ** term_months - 1)
    else:
        payment = amount / term_months

    debt_load = payment / monthly_income  # доля платежа от дохода

    return {
        "monthly_payment": round(payment, 2),
        "debt_load_percent": round(debt_load * 100, 1),
        "income_to_payment_ratio": round(monthly_income / payment, 2),
    }


def evaluate_rules(amount: float, monthly_income: float, term_months: int, calc: dict) -> dict:
    """
    Детерминированная проверка правил банка (в коде, не в LLM).
    Возвращает решение и список причин.
    """
    reasons = []
    approved = True

    # Правило: долговая нагрузка не выше 50%
    if calc["debt_load_percent"] > 50:
        approved = False
        reasons.append(f"долговая нагрузка {calc['debt_load_percent']}% превышает лимит 50%")

    # Правило: максимальная сумма 15 млн
    if amount > 15_000_000:
        approved = False
        reasons.append(f"сумма {amount} руб. превышает лимит 15 млн руб.")

    # Правило: срок 12-360 месяцев
    if term_months < 12 or term_months > 360:
        approved = False
        reasons.append(f"срок {term_months} мес. вне допустимого диапазона 12-360")

    # Правило: для суммы свыше 10 млн доход не менее 200к
    if amount > 10_000_000 and monthly_income < 200_000:
        approved = False
        reasons.append(f"для суммы свыше 10 млн требуется доход от 200к, а он {monthly_income}")

    return {
        "approved": approved,
        "reasons": reasons if reasons else ["все требования банка соблюдены"],
    }