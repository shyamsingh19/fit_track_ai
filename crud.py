from collections import defaultdict
from datetime import date, timedelta

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from models import MealEntry, WeightEntry
from schemas import MealEntryCreate, WeightEntryCreate


def add_meal(db: Session, data: MealEntryCreate):
    entry = MealEntry(**data.model_dump())
    db.add(entry)
    db.commit()
    return entry


def update_meal(db: Session, entry: MealEntry, data: MealEntryCreate):
    for key, value in data.model_dump().items():
        setattr(entry, key, value)
    db.commit()


def add_weight(db: Session, data: WeightEntryCreate):
    entry = WeightEntry(**data.model_dump())
    db.add(entry)
    db.commit()
    return entry


def update_weight(db: Session, entry: WeightEntry, data: WeightEntryCreate):
    for key, value in data.model_dump().items():
        setattr(entry, key, value)
    db.commit()


def delete_entry(db: Session, model, entry_id: int):
    entry = db.get(model, entry_id)
    if entry:
        db.delete(entry)
        db.commit()


def meals_for_day(db: Session, day: date):
    return db.scalars(
        select(MealEntry)
        .where(MealEntry.date == day)
        .order_by(MealEntry.created_at, MealEntry.id)
    ).all()


def search_meals(db: Session, query: str):
    filters = [MealEntry.food_name.ilike(f"%{query}%")]
    try:
        filters.append(MealEntry.date == date.fromisoformat(query))
    except ValueError:
        pass
    return db.scalars(
        select(MealEntry)
        .where(or_(*filters))
        .order_by(MealEntry.date.desc(), MealEntry.created_at.desc())
        .limit(100)
    ).all()


def recent_meals(db: Session, limit: int = 8):
    return db.scalars(
        select(MealEntry)
        .order_by(MealEntry.date.desc(), MealEntry.created_at.desc())
        .limit(limit)
    ).all()


def weight_history(db: Session):
    return db.scalars(
        select(WeightEntry).order_by(WeightEntry.date.desc(), WeightEntry.id.desc())
    ).all()


def daily_totals(db: Session, start: date, end: date):
    rows = db.execute(
        select(MealEntry.date, func.sum(MealEntry.protein))
        .where(MealEntry.date.between(start, end))
        .group_by(MealEntry.date)
    ).all()
    return {day: round(total, 2) for day, total in rows}


def date_series(start: date, end: date):
    return [start + timedelta(days=i) for i in range((end - start).days + 1)]


def average_for_period(totals: dict, start: date, end: date):
    days = date_series(start, end)
    return round(sum(totals.get(day, 0) for day in days) / len(days), 1)


def dashboard_stats(db: Session, today: date, goal: float):
    start_30 = today - timedelta(days=29)
    totals = daily_totals(db, start_30, today)
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)
    weights = weight_history(db)
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


def weekly_summary(db: Session, today: date):
    start = today - timedelta(days=today.weekday())
    totals = daily_totals(db, start, today)
    values = [totals.get(day, 0) for day in date_series(start, today)]
    weights = db.scalars(
        select(WeightEntry.weight).where(WeightEntry.date.between(start, today))
    ).all()
    return {
        "week": today.isocalendar().week,
        "average": round(sum(values) / len(values), 1),
        "highest": round(max(values), 1),
        "lowest": round(min(values), 1),
        "average_weight": round(sum(weights) / len(weights), 1) if weights else None,
    }


def analytics_data(db: Session, today: date, goal: float):
    start = today - timedelta(days=29)
    totals = daily_totals(db, start, today)
    days = date_series(start, today)
    protein_values = [totals.get(day, 0) for day in days]

    weekly = defaultdict(list)
    for day, value in zip(days, protein_values):
        year, week, _ = day.isocalendar()
        weekly[f"{year}-W{week:02d}"].append(value)

    weights = list(reversed(weight_history(db)[:90]))
    tracked_values = list(totals.values())
    adherence = (
        round(sum(value >= goal for value in tracked_values) / len(tracked_values) * 100)
        if tracked_values
        else 0
    )
    return {
        "protein_labels": [day.strftime("%b %d") for day in days],
        "protein_values": protein_values,
        "weekly_labels": list(weekly),
        "weekly_values": [round(sum(v) / len(v), 1) for v in weekly.values()],
        "weight_labels": [entry.date.strftime("%b %d") for entry in weights],
        "weight_values": [entry.weight for entry in weights],
        "adherence": adherence,
    }


def seed_sample_data(db: Session):
    if db.scalar(select(func.count()).select_from(MealEntry)):
        return False
    sample_day = date.today() - timedelta(days=1)
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
                date=sample_day,
                meal_type=meal_type,
                food_name=food,
                protein=protein,
            )
        )
    db.add(WeightEntry(date=sample_day, weight=54.7, notes="Sample weight"))
    db.commit()
    return True
