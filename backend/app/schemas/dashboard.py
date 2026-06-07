from pydantic import BaseModel


class DashboardResponse(BaseModel):
    today_protein: float
    today_calories: float
    today_fibre: float
    water: float | None
    sleep: float | None
    current_weight: float | None

    weekly_avg_protein: float | None
    weekly_avg_calories: float | None

