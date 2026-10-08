# Prompt: "Опиши две таблицы SQLAlchemy: measurements (id, distance, status, timestamp) и settings (key, value)"
# Prompt: "В measurements поле id — первичный ключ с автоинкрементом"
# Prompt: "В settings ключ key — первичный ключ"

from sqlalchemy import Column, Integer, Float, String
from app.database import Base


class Measurement(Base):
    __tablename__ = "measurements"
    id = Column(Integer, primary_key=True, index=True)
    distance = Column(Float)
    status = Column(String)
    timestamp = Column(String)


class Setting(Base):
    __tablename__ = "settings"
    key = Column(String, primary_key=True)
    value = Column(String)