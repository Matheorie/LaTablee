from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


class RegisterIn(BaseModel):
    email: str = Field(max_length=254, pattern=EMAIL_PATTERN)
    password: str = Field(min_length=8, max_length=72)
    display_name: str = Field(min_length=1, max_length=50)
    household_name: str | None = Field(default=None, min_length=1, max_length=100)
    invite_code: str | None = Field(default=None, min_length=1, max_length=20)

    @model_validator(mode="after")
    def household_or_invite(self):
        if (self.household_name is None) == (self.invite_code is None):
            raise ValueError("provide either household_name or invite_code")
        return self


class LoginIn(BaseModel):
    email: str = Field(max_length=254)
    password: str = Field(max_length=72)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    display_name: str
    household_id: int
    created_at: datetime


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class HouseholdOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    invite_code: str


class MemberOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    display_name: str
