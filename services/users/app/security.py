from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app import config
from app.models import User


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), password_hash.encode())
    except ValueError:
        return False


def create_token(user: User) -> str:
    """Jeton HS256 portant l'utilisateur, sa colocation et son nom."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user.id),
        "household_id": user.household_id,
        "name": user.display_name,
        "iat": now,
        "exp": now + timedelta(hours=config.JWT_TTL_HOURS),
    }
    return jwt.encode(payload, config.JWT_SECRET, algorithm="HS256")
