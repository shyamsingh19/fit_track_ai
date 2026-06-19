from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta, datetime, timezone

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from models import DietPlan, MealEntry, User, WeightEntry
from schemas import MealEntryCreate, WeightEntryCreate



def get_ist_date():
    return datetime.now(timezone(timedelta(hours=5, minutes=30))).date()


def add_meal(db: Session, user_id: int, data: MealEntryCreate) -> MealEntry:
    entry = MealEntry(user_id=user_id, **data.model_dump())
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def update_meal(db: Session, user_id: int, entry_id: int, data: MealEntryCreate):
    entry = db.scalar(
        select(MealEntry).where(MealEntry.id == entry_id, MealEntry.user_id == user_id)
    )
    if not entry:
        return None
    for key, value in data.model_dump().items():
        setattr(entry, key, value)
    db.commit()
    return entry


def add_weight(db: Session, user_id: int, data: WeightEntryCreate) -> WeightEntry:
    entry = WeightEntry(user_id=user_id, **data.model_dump())
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def update_weight(db: Session, user_id: int, entry_id: int, data: WeightEntryCreate):
    entry = db.scalar(
        select(WeightEntry).where(
            WeightEntry.id == entry_id, WeightEntry.user_id == user_id
        )
    )
    if not entry:
        return None
    for key, value in data.model_dump().items():
        setattr(entry, key, value)
    db.commit()
    return entry


def delete_entry(db: Session, user_id: int, model, entry_id: int) -> bool:
    # model must have id and user_id columns
    entry = db.scalar(
        select(model).where(model.id == entry_id, model.user_id == user_id)
    )
    if not entry:
        return False
    db.delete(entry)
    db.commit()
    return True


def meals_for_day(db: Session, user_id: int, day: date):
    return db.scalars(
        select(MealEntry)
        .where(MealEntry.user_id == user_id, MealEntry.date == day)
        .order_by(MealEntry.created_at, MealEntry.id)
    ).all()


def search_meals(db: Session, user_id: int, query: str):
    query = query.strip()
    filters = [MealEntry.user_id == user_id]
    if query:
        filters.append(MealEntry.food_name.ilike(f"%{query}%"))

    # Optional: if query parses as date, also match by date
    try:
        parsed = date.fromisoformat(query)
        filters.append(MealEntry.date == parsed)
        where_clause = or_(*filters)
    except ValueError:
        where_clause = filters[0] if len(filters) == 1 else or_(*filters)

    return db.scalars(
        select(MealEntry)
        .where(where_clause)
        .order_by(MealEntry.date.desc(), MealEntry.created_at.desc())
        .limit(100)
    ).all()


def recent_meals(db: Session, user_id: int, limit: int = 8):
    return db.scalars(
        select(MealEntry)
        .where(MealEntry.user_id == user_id)
        .order_by(MealEntry.date.desc(), MealEntry.created_at.desc())
        .limit(limit)
    ).all()


def weight_history(db: Session, user_id: int):
    return db.scalars(
        select(WeightEntry)
        .where(WeightEntry.user_id == user_id)
        .order_by(WeightEntry.date.desc(), WeightEntry.id.desc())
    ).all()


def daily_totals(db: Session, user_id: int, start: date, end: date):
    current_ist_date = get_ist_date()

    # Execute your standard database query
    rows = db.execute(
        select(MealEntry.date, func.sum(MealEntry.protein))
        .where(
            MealEntry.user_id == user_id,
            MealEntry.date.between(start, end),
        )
        .group_by(MealEntry.date)
    ).all()

    mapping = {day: round(total, 2) for day, total in rows}

    # Force 0 for today (IST) if no meals logged yet
    if current_ist_date not in mapping:
        mapping[current_ist_date] = 0.0

    return mapping


def date_series(start: date, end: date):
    return [start + timedelta(days=i) for i in range((end - start).days + 1)]


def average_for_period(totals: dict[date, float], start: date, end: date):
    days = date_series(start, end)
    return round(sum(totals.get(day_, 0) for day_ in days) / len(days), 1)


def dashboard_stats(db: Session, user_id: int, today: date, goal: float):
    start_30 = today - timedelta(days=29)
    totals = daily_totals(db, user_id, start_30, today)

    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)

    weights = weight_history(db, user_id)
    current = weights[0].weight if weights else None
    change = current - weights[1].weight if len(weights) > 1 else None

    today_total = totals.get(today, 0)
    return {
        "current_weight": current,
        "weight_change": change,
        "today_protein": today_total,
        "seven_day_average": average_for_period(
            totals, today - timedelta(days=6), today
        ),
        "week_average": average_for_period(totals, week_start, today),
        "month_average": average_for_period(totals, month_start, today),
        "goal_percent": min(round(today_total / goal * 100), 100),
    }


def weekly_summary(db: Session, user_id: int, today: date):
    start = today - timedelta(days=today.weekday())
    totals = daily_totals(db, user_id, start, today)
    values = [totals.get(day_, 0) for day_ in date_series(start, today)]

    weights = db.scalars(
        select(WeightEntry.weight).where(
            WeightEntry.user_id == user_id,
            WeightEntry.date.between(start, today),
        )
    ).all()

    return {
        "week": today.isocalendar().week,
        "average": round(sum(values) / len(values), 1),
        "highest": round(max(values), 1),
        "lowest": round(min(values), 1),
        "average_weight": round(sum(weights) / len(weights), 1) if weights else None,
    }


def analytics_data(db: Session, user_id: int, today: date, goal: float):
    start = today - timedelta(days=29)
    totals = daily_totals(db, user_id, start, today)
    days = date_series(start, today)
    protein_values = [totals.get(day_, 0) for day_ in days]

    weekly = defaultdict(list)
    for day_, value in zip(days, protein_values):
        year, week, _ = day_.isocalendar()
        weekly[f"{year}-W{week:02d}"].append(value)

    # Show up to 90 most recent weight entries for consistent chart sizing
    weights = list(reversed(weight_history(db, user_id)[:90]))

    tracked_values = list(totals.values())
    adherence = (
        round(
            sum(value >= goal for value in tracked_values) / len(tracked_values) * 100
        )
        if tracked_values
        else 0
    )

    return {
        "protein_labels": [day_.strftime("%b %d") for day_ in days],
        "protein_values": protein_values,
        "weekly_labels": list(weekly),
        "weekly_values": [round(sum(v) / len(v), 1) for v in weekly.values()],
        "weight_labels": [entry.date.strftime("%b %d") for entry in weights],
        "weight_values": [entry.weight for entry in weights],
        "adherence": adherence,
    }


def get_diet_plans(db: Session):
    return db.scalars(select(DietPlan).order_by(DietPlan.meal_type, DietPlan.id)).all()


def create_diet_plan(
    db: Session,
    meal_type: str,
    target_food: str,
    target_protein: float,
    notes: str | None = None,
) -> DietPlan:
    plan = DietPlan(
        meal_type=meal_type,
        target_food=target_food.strip(),
        target_protein=target_protein,
        notes=notes.strip() if isinstance(notes, str) else None,
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


def delete_diet_plan(db: Session, plan_id: int) -> bool:
    plan = db.scalar(select(DietPlan).where(DietPlan.id == plan_id))
    if not plan:
        return False
    db.delete(plan)
    db.commit()
    return True


def seed_sample_data(db: Session):
    """Seeds sample data for a single demo user (first user)."""
    user = db.scalar(select(User).order_by(User.id.asc()).limit(1))
    if not user:
        # no users => no seed
        return False


    if db.scalar(
        select(func.count()).select_from(MealEntry).where(MealEntry.user_id == user.id)
    ):
        return False

    sample_day = get_ist_date() - timedelta(days=1)
    meals = [
        ("Breakfast", "200ml milk", 6),
        ("Lunch", "PG lunch, curd rice", 10),
        ("Snack", "50g roasted chana", 10),
        ("Pre Workout", "Mix banana shake", 41.59),
        ("Dinner", "200g chola, 300g curd, 2 chapati, protein shake", 54.22),
    ]

    for meal_type, food, protein in meals:
        db.add(
            MealEntry(
                user_id=user.id,
                date=sample_day,
                meal_type=meal_type,
                food_name=food,
                protein=protein,
            )
        )

    db.add(
        WeightEntry(
            user_id=user.id, date=sample_day, weight=54.7, notes="Sample weight"
        )
    )
    db.commit()
    return True
