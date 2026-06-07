from datetime import date

from pydantic import BaseModel


class FoodLogRequest(BaseModel):
    date: date
    meal_type: str  # Breakfast/Lunch/Dinner/Snack
    raw_entry: str   # e.g. "Milk 300ml" or "2 chapati"


class FoodLogResponse(BaseModel):
    message: str

