from datetime import date
from typing import Optional

from pydantic import BaseModel


class WorkoutLogRequest(BaseModel):
    date: Optional[date] = None
    workout_type: str

    duration_minutes: float
    notes: Optional[str] = None






class WorkoutLogResponse(BaseModel):
    id: str
    message: str


class WorkoutHistoryItem(BaseModel):
    date: date
    workout_type: str
    duration_minutes: float
    notes: str | None = None


