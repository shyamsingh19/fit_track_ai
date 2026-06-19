from datetime import date

from pydantic import BaseModel, ConfigDict, Field


MEAL_TYPES = [
    "Breakfast",
    "Lunch",
    "Snack",
    "Pre Workout",
    "Post Workout",
    "Dinner",
    "Post Dinner",
    "Other",
]


class MealEntryCreate(BaseModel):
    date: date
    meal_type: str
    food_name: str = Field(min_length=1, max_length=250)
    protein: float = Field(ge=0, le=1000)
    notes: str | None = Field(default=None, max_length=2000)


class WeightEntryCreate(BaseModel):
    date: date
    weight: float = Field(gt=0, le=1000)
    notes: str | None = Field(default=None, max_length=2000)


class MealEntryRead(MealEntryCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int


class WeightEntryRead(WeightEntryCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
