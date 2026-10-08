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

# Prompt: "Добавь таблицу device_state для хранения текущего состояния устройства: distance, status, bad_since, last_update"
class DeviceState(Base):
    __tablename__ = "device_state"
    id = Column(Integer, primary_key=True)
    distance = Column(Float, default=0)
    status = Column(String, default="ok")
    bad_since = Column(String, nullable=True)
    last_update = Column(String, nullable=True)