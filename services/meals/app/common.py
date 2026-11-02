import logging

from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app import db

log = logging.getLogger(__name__)
router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    """Le processus répond."""
    return {"status": "ok"}


@router.get("/ready")
def ready():
    """La base répond et les tables existent."""
    if not db.state["initialized"]:
        raise HTTPException(status_code=503, detail="database not initialized")
    try:
        with db.engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except SQLAlchemyError:
        log.exception("readiness check failed")
        raise HTTPException(status_code=503, detail="database unavailable") from None
    return {"status": "ready"}


async def validation_handler(_request: Request, exc: RequestValidationError):
    """Une donnée invalide renvoie 400 et non le 422 par défaut de FastAPI."""
    errors = [{"loc": list(e["loc"]), "msg": e["msg"]} for e in exc.errors()]
    return JSONResponse(status_code=400, content={"detail": errors})


def install(app: FastAPI) -> None:
    app.add_exception_handler(RequestValidationError, validation_handler)
    app.include_router(router)
