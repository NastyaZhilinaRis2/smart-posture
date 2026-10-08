# Prompt: "Если два запроса придут одновременно, то данные могут перезаписаться. Поэтому перепиши state в базу. Создай таблицу device_state с одной строкой: distance, status, bad_since, last_update"
# Prompt: "Передавай сессию БД как аргумент функции, а не открывай SessionLocal внутри"

from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

from app.models import Setting, Measurement, DeviceState


def get_setting(db: Session, key: str, default) -> str:
    row = db.query(Setting).filter(Setting.key == key).first()
    if row is None:
        set_setting(db, key, default)
        return str(default)
    return row.value


def set_setting(db: Session, key: str, value) -> None:
    row = db.query(Setting).filter(Setting.key == key).first()
    if row is None:
        row = Setting(key=key, value=str(value))
        db.add(row)
    else:
        row.value = str(value)
    db.commit()


def get_state(db: Session) -> dict:
    row = db.query(DeviceState).first()
    if row is None:
        row = DeviceState(distance=0, status="ok", bad_since=None, last_update=None)
        db.add(row)
        db.commit()
        db.refresh(row)
    return {
        "distance": row.distance,
        "status": row.status,
        "bad_since": row.bad_since.isoformat() if row.bad_since else None,
        "last_update": row.last_update.isoformat() if row.last_update else None,
    }


def update_state(db: Session, distance=None, status=None, bad_since=None, last_update=None, set_bad_since=False) -> None:
    """Обновляет состояние в БД."""
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

    db.commit()


def check_posture(db: Session, distance: float) -> str:
    state = get_state(db)

    threshold = float(get_setting(db, "threshold", 10))
    duration = int(get_setting(db, "duration", 300))
    calibrated = float(get_setting(db, "calibrated", 40))

    diff = abs(distance - calibrated)
    is_bad_now = diff > threshold
    now = datetime.now()

    if is_bad_now:
        bad_since = state["bad_since"]
        if bad_since is None:
            bad_since_dt = now
        else:
            bad_since_dt = datetime.fromisoformat(bad_since)

        bad_seconds = (now - bad_since_dt).total_seconds()
        new_status = "bad" if bad_seconds >= duration else "warning"
        update_state(db, status=new_status, bad_since=bad_since_dt, set_bad_since=True)
    else:
        update_state(db, status="ok", bad_since=None, set_bad_since=True)

    return get_state(db)["status"]


def save_measurement(db: Session, distance: float, status: str, timestamp: datetime) -> None:
    m = Measurement(distance=distance, status=status, timestamp=timestamp)
    db.add(m)
    db.commit()