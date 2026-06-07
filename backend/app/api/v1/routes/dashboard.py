from datetime import date

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.api.v1.routes.auth import get_current_user_id
from app.db.session import get_db
from app.models.daily_metric import DailyMetric
from app.models.food_entry import FoodEntry
from app.schemas.dashboard import DashboardResponse

router = APIRouter()


@router.get("", response_model=DashboardResponse)
def dashboard(authorization: str | None = Header(default=None), db: Session = Depends(get_db)) -> DashboardResponse:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1]
    user_id = get_current_user_id(token)

    today = date.today().isoformat()

    food_rows = db.query(FoodEntry).filter(FoodEntry.user_id == user_id, FoodEntry.date == today).all()
    today_protein = sum(r.protein for r in food_rows)
    today_calories = sum(r.calories for r in food_rows)
    today_fibre = sum(r.fibre for r in food_rows)

    metric = db.query(DailyMetric).filter(DailyMetric.user_id == user_id, DailyMetric.date == today).first()
    water = metric.water_liters if metric else None
    sleep = metric.sleep_hours if metric else None
    current_weight = metric.weight if metric else None

    # last 7 days weekly average (including today)
    week_start = date.today().toordinal() - 6
    protein_sum = 0.0
    calories_sum = 0.0
    count_food_days = 0

    for i in range(7):
        d = date.fromordinal(week_start + i).isoformat()
        rows = db.query(FoodEntry).filter(FoodEntry.user_id == user_id, FoodEntry.date == d).all()
        if rows:
            protein_sum += sum(r.protein for r in rows)
            calories_sum += sum(r.calories for r in rows)
            count_food_days += 1

    weekly_avg_protein = round(protein_sum / count_food_days, 3) if count_food_days else None
    weekly_avg_calories = round(calories_sum / count_food_days, 3) if count_food_days else None

    return DashboardResponse(
        today_protein=round(today_protein, 3),
        today_calories=round(today_calories, 3),
        today_fibre=round(today_fibre, 3),
        water=water,
        sleep=sleep,
        current_weight=current_weight,
        weekly_avg_protein=weekly_avg_protein,
        weekly_avg_calories=weekly_avg_calories,
    )


