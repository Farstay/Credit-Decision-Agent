from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import Application, Decision, ApplicationStatus, DecisionType
from app.schemas import ApplicationCreate, ApplicationRead
from app.services.agent import analyze_application


router = APIRouter(prefix="/applications", tags=["applications"])


@router.post("", response_model=ApplicationRead, status_code=status.HTTP_201_CREATED)
async def create_application(data: ApplicationCreate, db: AsyncSession = Depends(get_db)):
    application = Application(**data.model_dump())
    db.add(application)
    await db.commit()
    await db.refresh(application)
    return application


@router.get("/{application_id}", response_model=ApplicationRead)
async def get_application(application_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Application)
        .where(Application.id == application_id)
        .options(selectinload(Application.decision))
    )
    application = result.scalar_one_or_none()
    if application is None:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    return application


@router.post("/{application_id}/analyze", response_model=ApplicationRead)
async def analyze(application_id: int, db: AsyncSession = Depends(get_db)):
    """Запустить AI-агента для анализа заявки и сохранить решение."""
    # находим заявку
    result = await db.execute(
        select(Application).where(Application.id == application_id)
    )
    application = result.scalar_one_or_none()
    if application is None:
        raise HTTPException(status_code=404, detail="Заявка не найдена")

    # если решение уже есть — не пересоздаём (идемпотентность)
    if application.decision is not None:
        return application

    # помечаем "в обработке"
    application.status = ApplicationStatus.processing
    await db.commit()

    try:
        # запускаем агента (передаём данные заявки)
        app_data = ApplicationCreate(
            applicant_name=application.applicant_name,
            amount=application.amount,
            monthly_income=application.monthly_income,
            purpose=application.purpose,
            term_months=application.term_months,
        )
        verdict = await analyze_application(app_data)

        # сохраняем решение
        decision = Decision(
            application_id=application.id,
            decision=DecisionType(verdict["decision"]),
            confidence=verdict["confidence"],
            reasoning=verdict["reasoning"],
        )
        db.add(decision)
        application.status = ApplicationStatus.completed
        await db.commit()
        await db.refresh(application, attribute_names=["decision"])
        return application

    except Exception as e:
        # обработка отказа: помечаем заявку как failed
        application.status = ApplicationStatus.failed
        await db.commit()
        raise HTTPException(status_code=500, detail=f"Ошибка анализа: {e}")