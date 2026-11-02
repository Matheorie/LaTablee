from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Meal(Base):
    __tablename__ = "meals"
    __table_args__ = (
        CheckConstraint("status IN ('open', 'closed', 'cancelled')", name="meals_status_check"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    household_id: Mapped[int] = mapped_column(Integer, index=True)
    title: Mapped[str] = mapped_column(String(120))
    menu: Mapped[str] = mapped_column(String(2000), default="")
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    booking_deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    cook_user_id: Mapped[int] = mapped_column(Integer)
    max_portions: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(10), default="open")
    series_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
