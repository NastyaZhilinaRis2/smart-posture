from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional
import sqlite3

app = FastAPI()

DB_PATH = "posture.db"

# ---------- База данных ----------

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS measurements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            distance REAL,
            status TEXT,
            timestamp TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    conn.commit()
    conn.close()

def get_setting(key, default):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = c.fetchone()
    conn.close()
    if row is None:
        set_setting(key, default)
        return default
    return row[0]

def set_setting(key, value):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
    conn.commit()
    conn.close()

init_db()

# ---------- Состояние ----------

state = {
    "distance": 0,
    "status": "ok",
    "bad_since": None,   # когда началось "криво"
    "last_update": None
}

# ---------- Модели ----------

class Measure(BaseModel):
    distance: float

class Settings(BaseModel):
    threshold: Optional[float] = None
    duration: Optional[int] = None

# ---------- Логика ----------

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

# ---------- Эндпоинты ----------

@app.get("/")
def root():
    return {"message": "Posture server is running"}

@app.post("/measure")
def measure(data: Measure):
    check_posture(data.distance)

    state["distance"] = data.distance
    state["last_update"] = datetime.now().isoformat()

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO measurements (distance, status, timestamp) VALUES (?, ?, ?)",
        (data.distance, state["status"], state["last_update"])
    )
    conn.commit()
    conn.close()

    return {"status": "ok", "current": state["status"]}

@app.get("/status")
def status():
    return state

@app.get("/stats")
def stats():
    today = date.today().isoformat()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "SELECT status, COUNT(*) FROM measurements WHERE timestamp LIKE ? GROUP BY status",
        (today + "%",)
    )
    rows = c.fetchall()
    conn.close()

    counts = {row[0]: row[1] for row in rows}
    total = sum(counts.values())

    # Предполагаем, что датчик шлёт данные раз в 2 секунды
    seconds_per_sample = 2
    good_seconds = (counts.get("ok", 0) + counts.get("warning", 0)) * seconds_per_sample
    bad_seconds = counts.get("bad", 0) * seconds_per_sample

    return {
        "date": today,
        "total_samples": total,
        "good_minutes": round(good_seconds / 60, 1),
        "bad_minutes": round(bad_seconds / 60, 1)
    }

@app.get("/settings")
def get_settings():
    return {
        "threshold": float(get_setting("threshold", 10)),
        "duration": int(get_setting("duration", 300)),
        "calibrated": float(get_setting("calibrated", 40))
    }

@app.post("/settings")
def update_settings(new: Settings):
    if new.threshold is not None:
        set_setting("threshold", new.threshold)
    if new.duration is not None:
        set_setting("duration", new.duration)
    return get_settings()

@app.post("/calibrate")
def calibrate():
    set_setting("calibrated", state["distance"])
    return {"status": "calibrated", "distance": state["distance"]}