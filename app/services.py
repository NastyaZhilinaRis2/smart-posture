# Prompt: "Напиши функции get_setting и set_setting для чтения и записи настроек в базу"
# Prompt: "Если настройки нет в базе, создай её со значением по умолчанию"
# Prompt: "Опиши глобальный словарь state для хранения текущего расстояния, статуса и времени начала плохой осанки"
# Prompt: "Напиши функцию check_posture: сравни расстояние с калибровкой, если отклонение больше порога — статус warning, если это длится дольше duration — статус bad, иначе ok"
# Prompt: "Добавь функцию save_measurement, которая сохраняет измерение в базу"

from datetime import datetime

from app.database import SessionLocal
from app.models import Setting, Measurement


state = {
    "distance": 0,
    "status": "ok",
    "bad_since": None,
    "last_update": None
}


def get_setting(key, default):
    db = SessionLocal()
    try:
        row = db.query(Setting).filter(Setting.key == key).first()
        if row is None:
            set_setting(key, default)
            return default
        return row.value
    finally:
        db.close()


def set_setting(key, value):
    db = SessionLocal()
    try:
        row = db.query(Setting).filter(Setting.key == key).first()
        if row is None:
            row = Setting(key=key, value=str(value))
            db.add(row)
        else:
            row.value = str(value)
        db.commit()
    finally:
        db.close()


def check_posture(distance: float):
    threshold = float(get_setting("threshold", 10))
    duration = int(get_setting("duration", 300))
    calibrated = float(get_setting("calibrated", 40))

    diff = abs(distance - calibrated)
    is_bad_now = diff > threshold
    now = datetime.now()

    if is_bad_now:
        if state["bad_since"] is None:
            state["bad_since"] = now
        bad_seconds = (now - state["bad_since"]).total_seconds()
        if bad_seconds >= duration:
            state["status"] = "bad"
        else:
            state["status"] = "warning"
    else:
        state["bad_since"] = None
        state["status"] = "ok"


def save_measurement(distance: float, status: str, timestamp: str):
    db = SessionLocal()
    try:
        m = Measurement(distance=distance, status=status, timestamp=timestamp)
        db.add(m)
        db.commit()
    finally:
        db.close()