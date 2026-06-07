import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.core.config import settings


@dataclass(frozen=True)
class NutritionFacts:
    protein: float
    calories: float
    fibre: float


class NutritionService:
    def __init__(self, data_path: str | None = None):
        if data_path is None:
            data_path = os.getenv("NUTRITION_DATA_PATH")
        if data_path is None:
            data_path = str(Path(__file__).resolve().parents[1] / "data" / "nutrition.json")

        self._data = self._load(data_path)

    def _load(self, path: str) -> dict[str, NutritionFacts]:
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)

        out: dict[str, NutritionFacts] = {}
        for k, v in raw.items():
            out[k.lower().strip()] = NutritionFacts(
                protein=float(v["protein"]),
                calories=float(v["calories"]),
                fibre=float(v.get("fibre", 0.0)),
            )
        return out

    def lookup(self, food_name: str) -> NutritionFacts:
        key = self.normalize_food_key(food_name)
        if key not in self._data:
            raise KeyError(f"Unknown food: {food_name}")
        return self._data[key]

    @staticmethod
    def normalize_food_key(food_name: str) -> str:
        s = food_name.lower().strip()
        s = re.sub(r"[^a-z0-9]+", " ", s)
        s = s.strip()
        return s

    @staticmethod
    def parse_quantity(value: float, unit: str | None) -> float:
        """Return grams-equivalent or ml-equivalent scale.

        MVP simplification:
        - If unit is g / gram => scale is grams
        - If unit is ml / milliliter => scale is ml
        - If unit is none or unknown => treat as grams

        Nutrition.json values are per 100g/100ml.
        """
        if unit is None:
            return value
        u = unit.lower().strip()
        if u in {"g", "gram", "grams"}:
            return value
        if u in {"ml", "milliliter", "milliliters"}:
            return value
        # roti/egg/scoop/unitless MVP: treat as 1 serving scaled by value
        return value

    def calculate(self, food_name: str, quantity: float, unit: str | None) -> NutritionFacts:
        facts = self.lookup(food_name)
        scale = self.parse_quantity(quantity, unit)
        factor = scale / 100.0
        return NutritionFacts(
            protein=round(facts.protein * factor, 3),
            calories=round(facts.calories * factor, 3),
            fibre=round(facts.fibre * factor, 3),
        )


nutrition_service = NutritionService()

