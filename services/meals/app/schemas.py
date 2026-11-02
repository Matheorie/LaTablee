from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


def as_utc(value: datetime) -> datetime:
    """Une date sans fuseau est interprétée comme UTC."""
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


class MealCreate(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    menu: str = Field(default="", max_length=2000)
    starts_at: datetime
    booking_deadline: datetime
    cook_user_id: int | None = None
    max_portions: int | None = Field(default=None, ge=1)
    repeat_weeks: int = Field(default=1, ge=1, le=12)

    _utc = field_validator("starts_at", "booking_deadline")(as_utc)

    @model_validator(mode="after")
    def deadline_before_start(self):
        if self.booking_deadline > self.starts_at:
            raise ValueError("booking_deadline must not be after starts_at")
        return self


class MealUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=120)
    menu: str | None = Field(default=None, max_length=2000)
    starts_at: datetime | None = None
    booking_deadline: datetime | None = None
    cook_user_id: int | None = None
    max_portions: int | None = Field(default=None, ge=1)

    @field_validator("starts_at", "booking_deadline")
    @classmethod
    def _utc(cls, value):
        return None if value is None else as_utc(value)


class MealOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    household_id: int
    title: str
    menu: str
    starts_at: datetime
    booking_deadline: datetime
    cook_user_id: int
    max_portions: int | None
    status: str
    series_id: str | None
    created_at: datetime
