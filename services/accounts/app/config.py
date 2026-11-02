import os
from urllib.parse import quote_plus

JWT_SECRET = os.environ["JWT_SECRET"]
JWT_TTL_HOURS = int(os.environ.get("JWT_TTL_HOURS", "24"))
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
ROOT_PATH = os.environ.get("ROOT_PATH", "")
MEALS_URL = os.environ.get("MEALS_URL", "http://meals:8000")
BOOKINGS_URL = os.environ.get("BOOKINGS_URL", "http://bookings:8000")
SERVICE_TIMEOUT = 3.0


def database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if url:
        return url
    user = quote_plus(os.environ["DB_USER"])
    password = quote_plus(os.environ["DB_PASSWORD"])
    host = os.environ.get("DB_HOST", "postgres")
    port = os.environ.get("DB_PORT", "5432")
    name = os.environ["DB_NAME"]
    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{name}"
