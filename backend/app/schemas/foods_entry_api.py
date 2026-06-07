from datetime import date
from typing import Optional

from pydantic import BaseModel


class FoodEntryCreateRequest(BaseModel):
    date: Optional[date] = None
    meal_type: str
    food_name: str
    quantity: float
    unit: str | None = None


class FoodEntryResponse(BaseModel):
    id: str
    date: date
    meal_type: str
    food_name: str
    quantity: float
    unit: str | None
    protein: float
    calories: float
    fibre: float


class FoodSummaryResponse(BaseModel):
    protein: float
    calories: float
    fibre: float

