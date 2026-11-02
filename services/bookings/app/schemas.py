from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class BookingIn(BaseModel):
    portions: int = Field(ge=1, le=20)


class BookingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    meal_id: int
    user_id: int
    portions: int
    created_at: datetime
    updated_at: datetime


class ParticipantOut(BaseModel):
    user_id: int
    portions: int


class MealBookingsOut(BaseModel):
    meal_id: int
    total_portions: int
    participants: list[ParticipantOut]
