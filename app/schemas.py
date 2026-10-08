# Prompt: "Опиши Pydantic-схемы для приёма данных: Measure с полем distance и Settings с полями threshold и duration"
# Prompt: "Поля в Settings должны быть необязательными, чтобы можно было менять их по отдельности"

from pydantic import BaseModel
from typing import Optional


class Measure(BaseModel):
    distance: float


class Settings(BaseModel):
    threshold: Optional[float] = None
    duration: Optional[int] = None