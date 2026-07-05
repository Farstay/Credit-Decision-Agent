import enum
from datetime import datetime
from sqlalchemy import String, Integer, Float, ForeignKey, Enum, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base



class ApplicationStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"



class DecisionType(str, enum.Enum):
    approved = "approved"
    rejected = "rejected"



class Application(Base):
    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(primary_key=True)
    applicant_name: Mapped[str] = mapped_column(String(100))
    amount: Mapped[float] = mapped_column(Float)
    monthly_income: Mapped[float] = mapped_column(Float)
    purpose: Mapped[str] = mapped_column(String(255))
    term_months: Mapped[int] = mapped_column(Integer)
    status: Mapped[ApplicationStatus] = mapped_column(
        Enum(ApplicationStatus, native_enum=False, length=20),
        default=ApplicationStatus.pending,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    decision: Mapped["Decision | None"] = relationship(
        back_populates="application", lazy="selectin"
    )




class Decision(Base):
    __tablename__ = "decisions"

    id: Mapped[int] = mapped_column(primary_key=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("applications.id"))
    decision: Mapped[DecisionType] = mapped_column(Enum(DecisionType, native_enum=False, length=20))
    confidence: Mapped[float] = mapped_column(Float)
    reasoning: Mapped[str] = mapped_column(String(2000))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    application: Mapped["Application"] = relationship(back_populates="decision")