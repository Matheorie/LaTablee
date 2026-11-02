import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import config, db
from app.common import install
from app.routes import router

logging.basicConfig(level=config.LOG_LEVEL, format="%(asctime)s %(levelname)s %(name)s %(message)s")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    db.start_init_in_background()
    yield


app = FastAPI(title="LaTablee bookings", root_path=config.ROOT_PATH, lifespan=lifespan)
install(app)
app.include_router(router)
