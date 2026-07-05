from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from app.models import ApplicationStatus, DecisionType



class ApplicationCreate(BaseModel):
    applicant_name: str = Field(min_length=1, max_length=100)
    amount: float = Field(gt=0, description="Запрашиваемая сумма, > 0")
    monthly_income: float = Field(gt=0, description="Месячный доход, > 0")
    purpose: str = Field(min_length=1, max_length=255)
    term_months: int = Field(gt=0, le=360, description="Срок в месяцах, 1..360")



class DecisionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # разрешить чтение из ORM-объекта

    id: int
    decision: DecisionType
    confidence: float
    reasoning: str
    created_at: datetime



class ApplicationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    applicant_name: str
    amount: float
    monthly_income: float
    purpose: str
    term_months: int
    status: ApplicationStatus
    created_at: datetime
    decision: DecisionRead | None = None  # решение может ещё не быть готово