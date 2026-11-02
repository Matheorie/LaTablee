from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Expense(Base):
    __tablename__ = "expenses"
    __table_args__ = (CheckConstraint("amount_cents > 0", name="expenses_amount_check"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    household_id: Mapped[int] = mapped_column(Integer, index=True)
    meal_id: Mapped[int] = mapped_column(Integer, unique=True)
    paid_by: Mapped[int] = mapped_column(Integer)
    amount_cents: Mapped[int] = mapped_column(Integer)
    description: Mapped[str] = mapped_column(String(200), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    shares: Mapped[list["Share"]] = relationship(
        back_populates="expense", cascade="all, delete-orphan", order_by="Share.user_id"
    )


class Share(Base):
    __tablename__ = "shares"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    expense_id: Mapped[int] = mapped_column(ForeignKey("expenses.id"))
    user_id: Mapped[int] = mapped_column(Integer)
    portions: Mapped[int] = mapped_column(Integer)
    amount_cents: Mapped[int] = mapped_column(Integer)

    expense: Mapped[Expense] = relationship(back_populates="shares")


class Payment(Base):
    __tablename__ = "payments"
    __table_args__ = (
        CheckConstraint("from_user <> to_user", name="payments_users_check"),
        CheckConstraint("amount_cents > 0", name="payments_amount_check"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    household_id: Mapped[int] = mapped_column(Integer, index=True)
    from_user: Mapped[int] = mapped_column(Integer)
    to_user: Mapped[int] = mapped_column(Integer)
    amount_cents: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
