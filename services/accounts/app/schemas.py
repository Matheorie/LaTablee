from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ExpenseIn(BaseModel):
    meal_id: int
    amount_cents: int = Field(gt=0)
    description: str = Field(default="", max_length=200)
    paid_by: int | None = None


class ShareOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    portions: int
    amount_cents: int


class ExpenseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    household_id: int
    meal_id: int
    paid_by: int
    amount_cents: int
    description: str
    created_at: datetime
    shares: list[ShareOut]


class BalanceOut(BaseModel):
    user_id: int
    balance_cents: int


class SettlementOut(BaseModel):
    from_user: int
    to_user: int
    amount_cents: int


class PaymentIn(BaseModel):
    to_user: int
    amount_cents: int = Field(gt=0)


class PaymentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    household_id: int
    from_user: int
    to_user: int
    amount_cents: int
    created_at: datetime
