# Prompt: "Создай APIRouter и вынеси в него все эндпоинты FastAPI"
# Prompt: "GET / — проверка, что сервер жив"
# Prompt: "POST /measure — принимает расстояние, вызывает check_posture, сохраняет измерение и возвращает текущий статус"
# Prompt: "GET /status — возвращает текущее состояние из state"
# Prompt: "GET /stats — считает за сегодня количество измерений по статусам и переводит в минуты, предполагая что датчик шлёт данные раз в 2 секунды"
# Prompt: "GET /alerts — возвращает последние N случаев плохой осанки (status='bad') из базы, по умолчанию 10"
# Prompt: "GET /settings — возвращает текущие настройки из базы"
# Prompt: "POST /settings — обновляет только те поля, которые пришли в запросе"
# Prompt: "POST /calibrate — сохраняет текущее расстояние как правильное"

from datetime import datetime, date

from fastapi import APIRouter

from app.database import SessionLocal
from app.models import Measurement
from app.schemas import Measure, Settings
from app.services import (
    state,
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
def measure(data: Measure):
    check_posture(data.distance)
    state["distance"] = data.distance
    state["last_update"] = datetime.now().isoformat()
    save_measurement(data.distance, state["status"], state["last_update"])
    return {"status": "ok", "current": state["status"]}


@router.get("/status")
def status():
    return state


@router.get("/stats")
def stats():
    today = date.today().isoformat()
    db = SessionLocal()
    try:
        rows = db.query(Measurement).filter(Measurement.timestamp.like(today + "%")).all()
    finally:
        db.close()

    counts = {}
    for row in rows:
        counts[row.status] = counts.get(row.status, 0) + 1
    total = sum(counts.values())

    seconds_per_sample = 2
    good_seconds = (counts.get("ok", 0) + counts.get("warning", 0)) * seconds_per_sample
    bad_seconds = counts.get("bad", 0) * seconds_per_sample

    return {
        "date": today,
        "total_samples": total,
        "good_minutes": round(good_seconds / 60, 1),
        "bad_minutes": round(bad_seconds / 60, 1)
    }


@router.get("/alerts")
def alerts(limit: int = 10):
    db = SessionLocal()
    try:
        rows = (
            db.query(Measurement)
            .filter(Measurement.status == "bad")
            .order_by(Measurement.id.desc())
            .limit(limit)
            .all()
        )
    finally:
        db.close()

    return {
        "count": len(rows),
        "alerts": [
            {"id": r.id, "distance": r.distance, "timestamp": r.timestamp}
            for r in rows
        ]
    }


@router.get("/settings")
def get_settings():
    return {
        "threshold": float(get_setting("threshold", 10)),
        "duration": int(get_setting("duration", 300)),
        "calibrated": float(get_setting("calibrated", 40))
    }


@router.post("/settings")
def update_settings(new: Settings):
    if new.threshold is not None:
        set_setting("threshold", new.threshold)
    if new.duration is not None:
        set_setting("duration", new.duration)
    return get_settings()


@router.post("/calibrate")
def calibrate():
    set_setting("calibrated", state["distance"])
    return {"status": "calibrated", "distance": state["distance"]}