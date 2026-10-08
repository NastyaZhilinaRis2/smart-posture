# Prompt: "Создай APIRouter и вынеси в него все эндпоинты FastAPI"
# Prompt: "GET / — проверка, что сервер жив"
# Prompt: "POST /measure — принимает расстояние, вызывает check_posture, сохраняет измерение и возвращает текущий статус"
# Prompt: "GET /status — возвращает текущее состояние из state"
# Prompt: "GET /stats — считает за сегодня количество измерений по статусам и переводит в минуты, предполагая что датчик шлёт данные раз в 2 секунды"
# Prompt: "GET /alerts — возвращает последние N случаев плохой осанки (status='bad') из базы, по умолчанию 10"
# Prompt: "GET /settings — возвращает текущие настройки из базы"
# Prompt: "POST /settings — обновляет только те поля, которые пришли в запросе"
# Prompt: "POST /calibrate — сохраняет текущее расстояние как правильное"

# Prompt: "Перепиши эндпоинты так, чтобы состояние устройства читалось и писалось через get_state и update_state из базы данных, а не через глобальный словарь state"

from datetime import datetime, date, time

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Measurement
from app.schemas import Measure, Settings
from app.services import (
    get_state,
    update_state,
    get_setting,
    set_setting,
    check_posture,
    save_measurement,
)

router = APIRouter()


@router.get("/")
def root():
    return {"message": "Posture server is running"}


@router.post("/measure")
def measure(data: Measure, db: Session = Depends(get_db)):
    new_status = check_posture(db, data.distance)
    now = datetime.now()
    update_state(db, distance=data.distance, last_update=now)
    save_measurement(db, data.distance, new_status, now)
    return {"status": "ok", "current": new_status}


@router.get("/status")
def status(db: Session = Depends(get_db)):
    return get_state(db)


@router.get("/stats")
def stats(db: Session = Depends(get_db)):
    today = date.today()
    start = datetime.combine(today, time.min)
    end = datetime.combine(today, time.max)

    rows = db.query(Measurement).filter(
        Measurement.timestamp >= start,
        Measurement.timestamp <= end
    ).all()

    counts = {}
    for row in rows:
        counts[row.status] = counts.get(row.status, 0) + 1
    total = sum(counts.values())

    seconds_per_sample = 2
    good_seconds = (counts.get("ok", 0) + counts.get("warning", 0)) * seconds_per_sample
    bad_seconds = counts.get("bad", 0) * seconds_per_sample

    return {
        "date": today.isoformat(),
        "total_samples": total,
        "good_minutes": round(good_seconds / 60, 1),
        "bad_minutes": round(bad_seconds / 60, 1)
    }


@router.get("/alerts")
def alerts(limit: int = 10, db: Session = Depends(get_db)):
    rows = (
        db.query(Measurement)
        .filter(Measurement.status == "bad")
        .order_by(Measurement.id.desc())
        .limit(limit)
        .all()
    )

    return {
        "count": len(rows),
        "alerts": [
            {"id": r.id, "distance": r.distance, "timestamp": r.timestamp.isoformat()}
            for r in rows
        ]
    }


@router.get("/settings")
def get_settings(db: Session = Depends(get_db)):
    return {
        "threshold": float(get_setting(db, "threshold", 10)),
        "duration": int(get_setting(db, "duration", 300)),
        "calibrated": float(get_setting(db, "calibrated", 40))
    }


@router.post("/settings")
def update_settings(new: Settings, db: Session = Depends(get_db)):
    if new.threshold is not None:
        set_setting(db, "threshold", new.threshold)
    if new.duration is not None:
        set_setting(db, "duration", new.duration)
    return get_settings(db)


@router.post("/calibrate")
def calibrate(db: Session = Depends(get_db)):
    state = get_state(db)
    set_setting(db, "calibrated", state["distance"])
    return {"status": "calibrated", "distance": state["distance"]}