# Prompt: "Если два запроса придут одновременно, то данные могут перезаписаться. Поэтому перепиши state в базу. Создай таблицу device_state с одной строкой: distance, status, bad_since, last_update"

from datetime import datetime

from app.database import SessionLocal
from app.models import Setting, Measurement, DeviceState


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


def get_state():
    db = SessionLocal()
    try:
        row = db.query(DeviceState).first()
        if row is None:
            row = DeviceState(distance=0, status="ok", bad_since=None, last_update=None)
            db.add(row)
            db.commit()
            db.refresh(row)
        return {
            "distance": row.distance,
            "status": row.status,
            "bad_since": row.bad_since,
            "last_update": row.last_update,
        }
    finally:
        db.close()


def update_state(distance=None, status=None, bad_since=None, last_update=None, set_bad_since=False):
    """Обновляет состояние в БД."""
    db = SessionLocal()
    try:
        row = db.query(DeviceState).first()
        if row is None:
            row = DeviceState()
            db.add(row)

        if distance is not None:
            row.distance = distance
        if status is not None:
            row.status = status
        if last_update is not None:
            row.last_update = last_update
        if set_bad_since:
            row.bad_since = bad_since
        elif bad_since is not None:
            row.bad_since = bad_since

        db.commit()
    finally:
        db.close()


def check_posture(distance: float):
    state = get_state()

    threshold = float(get_setting("threshold", 10))
    duration = int(get_setting("duration", 300))
    calibrated = float(get_setting("calibrated", 40))

    diff = abs(distance - calibrated)
    is_bad_now = diff > threshold
    now = datetime.now()

    if is_bad_now:
        bad_since_str = state["bad_since"]
        if bad_since_str is None:
            bad_since_dt = now
            bad_since_str = now.isoformat()
        else:
            bad_since_dt = datetime.fromisoformat(bad_since_str)

        bad_seconds = (now - bad_since_dt).total_seconds()
        if bad_seconds >= duration:
            new_status = "bad"
        else:
            new_status = "warning"

        update_state(status=new_status, bad_since=bad_since_str)
    else:
        update_state(status="ok", bad_since=None)

    return get_state()["status"]


def save_measurement(distance: float, status: str, timestamp: str):
    db = SessionLocal()
    try:
        m = Measurement(distance=distance, status=status, timestamp=timestamp)
        db.add(m)
        db.commit()
    finally:
        db.close()