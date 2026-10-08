# Prompt: "Напиши подключение к базе данных через SQLAlchemy"
# Prompt: "Сделай так, чтобы локально использовалась SQLite, а на Railway — PostgreSQL через переменную окружения DATABASE_URL"
# Prompt: "Добавь замену postgres:// на postgresql://, потому что Railway отдаёт старый формат"
# Prompt: "Создай функцию get_db, которая открывает сессию и закрывает её после использования"

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./posture.db")

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()