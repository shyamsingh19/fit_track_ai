from datetime import date, datetime

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.food_entry import FoodEntry
from app.schemas.foods import FoodLogRequest, FoodLogResponse
from app.schemas.foods_entry_api import FoodEntryCreateRequest, FoodEntryResponse, FoodSummaryResponse
from app.services.nutrition_service import NutritionService

from app.api.v1.routes.auth import get_current_user_id

router = APIRouter()

nutrition = NutritionService()


def _default_today() -> str:
    return date.today().isoformat()


@router.post("", response_model=FoodEntryResponse)
def create_food_entry(req: FoodEntryCreateRequest, authorization: str | None = Header(default=None), db: Session = Depends(get_db)) -> FoodEntryResponse:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1]
    user_id = get_current_user_id(token)

    d = req.date.isoformat() if req.date else _default_today()

    try:
        facts = nutrition.calculate(req.food_name, req.quantity, req.unit)
    except KeyError:
        raise HTTPException(status_code=400, detail="Unknown food")

    entry = FoodEntry(
        user_id=user_id,
        date=d,
        meal_type=req.meal_type,
        food_name=req.food_name,
        quantity=req.quantity,
        unit=req.unit,
        protein=facts.protein,
        calories=facts.calories,
        fibre=facts.fibre,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)

    return FoodEntryResponse(
        id=str(entry.id),
        date=date.fromisoformat(entry.date),
        meal_type=entry.meal_type,
        food_name=entry.food_name,
        quantity=entry.quantity,
        unit=entry.unit,
        protein=entry.protein,
        calories=entry.calories,
        fibre=entry.fibre,
    )


@router.get("", response_model=list[FoodEntryResponse])
def get_food_entries_today(authorization: str | None = Header(default=None), db: Session = Depends(get_db)) -> list[FoodEntryResponse]:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1]
    user_id = get_current_user_id(token)

    today = date.today().isoformat()
    rows = db.query(FoodEntry).filter(FoodEntry.user_id == user_id, FoodEntry.date == today).order_by(FoodEntry.created_at.desc()).all()

    out: list[FoodEntryResponse] = []
    for entry in rows:
        out.append(
            FoodEntryResponse(
                id=str(entry.id),
                date=date.fromisoformat(entry.date),
                meal_type=entry.meal_type,
                food_name=entry.food_name,
                quantity=entry.quantity,
                unit=entry.unit,
                protein=entry.protein,
                calories=entry.calories,
                fibre=entry.fibre,
            )
        )
    return out


@router.get("/summary", response_model=FoodSummaryResponse)
def daily_summary(authorization: str | None = Header(default=None), db: Session = Depends(get_db)) -> FoodSummaryResponse:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1]
    user_id = get_current_user_id(token)

    today = date.today().isoformat()
    rows = db.query(FoodEntry).filter(FoodEntry.user_id == user_id, FoodEntry.date == today).all()

    protein = sum(r.protein for r in rows)
    calories = sum(r.calories for r in rows)
    fibre = sum(r.fibre for r in rows)

    return FoodSummaryResponse(protein=round(protein, 3), calories=round(calories, 3), fibre=round(fibre, 3))


@router.delete("/{entry_id}")
def delete_food_entry(entry_id: str, authorization: str | None = Header(default=None), db: Session = Depends(get_db)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1]
    user_id = get_current_user_id(token)

    row = db.query(FoodEntry).filter(FoodEntry.id == entry_id, FoodEntry.user_id == user_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Not found")

    db.delete(row)
    db.commit()
    return FoodLogResponse(message="Deleted")


