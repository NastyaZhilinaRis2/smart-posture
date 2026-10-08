# Prompt: "Опиши Pydantic-схемы для приёма данных: Measure с полем distance и Settings с полями threshold и duration"
# Prompt: "Поля в Settings должны быть необязательными, чтобы можно было менять их по отдельности"

from pydantic import BaseModel, Field
from typing import Optional


class Measure(BaseModel):
    distance: float = Field(ge=0, le=500, description="Расстояние в см")


class Settings(BaseModel):
    threshold: Optional[float] = Field(default=None, ge=0, le=100)
    duration: Optional[int] = Field(default=None, ge=1, le=3600)