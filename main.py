# Prompt: "Собери FastAPI-приложение"
# Prompt: "Создай таблицы в базе при старте"

from fastapi import FastAPI

from app.database import Base, engine
from app import models  # noqa: F401
from app.routes import router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Posture server")

app.include_router(router)