from dataclasses import dataclass

import jwt
from fastapi import Header, HTTPException

from app import config


@dataclass
class CurrentUser:
    id: int
    household_id: int
    name: str
    token: str


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=401,
        detail="invalid or missing token",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(authorization: str | None = Header(default=None)) -> CurrentUser:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise _unauthorized()
    token = authorization[7:].strip()
    try:
        claims = jwt.decode(token, config.JWT_SECRET, algorithms=["HS256"])
        return CurrentUser(
            id=int(claims["sub"]),
            household_id=int(claims["household_id"]),
            name=str(claims.get("name", "")),
            token=token,
        )
    except (jwt.PyJWTError, KeyError, ValueError, TypeError):
        raise _unauthorized() from None
