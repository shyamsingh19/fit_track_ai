from datetime import date
from typing import Optional

from pydantic import BaseModel


class WeightLogRequest(BaseModel):
    date: Optional[date] = None
    weight: float







class WeightLogResponse(BaseModel):
    id: str
    message: str


class WeightHistoryItem(BaseModel):
    date: date
    weight: float


