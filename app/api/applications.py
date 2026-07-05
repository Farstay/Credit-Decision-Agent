from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import Application
from app.schemas import ApplicationCreate, ApplicationRead

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