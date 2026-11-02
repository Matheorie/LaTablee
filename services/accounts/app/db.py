import logging
import threading
import time

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import StaticPool

from app import config

log = logging.getLogger(__name__)

_url = config.database_url()
if _url.startswith("sqlite"):
    engine = create_engine(_url, connect_args={"check_same_thread": False}, poolclass=StaticPool)
else:
    engine = create_engine(_url, pool_pre_ping=True)

SessionLocal = sessionmaker(bind=engine, autoflush=False)

# Passe à True quand les tables existent. Sert à la sonde /ready.
state = {"initialized": False}


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db(retries: int = 60, delay: float = 2.0) -> None:
    """Crée les tables, en réessayant tant que PostgreSQL n'est pas prêt."""
    from app import models  # noqa: F401  (enregistre les tables sur Base)

    for attempt in range(1, retries + 1):
        try:
            Base.metadata.create_all(engine)
            state["initialized"] = True
            log.info("database initialized")
            return
        except Exception as exc:  # noqa: BLE001
            log.warning("database not ready (%s/%s): %s", attempt, retries, exc)
            time.sleep(delay)
    log.error("database initialization abandoned")


def start_init_in_background() -> None:
    threading.Thread(target=init_db, daemon=True).start()
