# Prompt: "Настрой pytest так, чтобы каждый тест использовал чистую тестовую базу данных"
# Prompt: "Перед каждым тестом создавай таблицы заново, после — удаляй"

import os
import pytest

os.environ["DATABASE_URL"] = "sqlite:///./test.db"

from app.database import Base, engine, SessionLocal
from app import models  # noqa: F401


@pytest.fixture(autouse=True)
def clean_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)