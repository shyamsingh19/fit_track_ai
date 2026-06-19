import os
from contextlib import asynccontextmanager
from datetime import date

from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from sqlalchemy.orm import Session

import crud
from database import Base, SessionLocal, engine, get_db
from models import MealEntry, WeightEntry
from schemas import MEAL_TYPES, MealEntryCreate, WeightEntryCreate


try:
    PROTEIN_GOAL = float(os.getenv("PROTEIN_GOAL", "120"))
    if PROTEIN_GOAL <= 0:
        raise ValueError
except ValueError as exc:
    raise RuntimeError("PROTEIN_GOAL must be a positive number") from exc


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(engine)
    if os.getenv("SEED_SAMPLE_DATA") == "1":
        with SessionLocal() as db:
            crud.seed_sample_data(db)
    yield


app = FastAPI(title="Protein Tracker", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


def render(request: Request, template: str, **context):
    return templates.TemplateResponse(
        request=request,
        name=template,
        context={
            "goal": PROTEIN_GOAL,
            "today": date.today(),
            **context,
        },
    )


def clean_notes(notes: str):
    return notes.strip() or None


def meal_data(day, meal_type, food_name, protein, notes):
    if meal_type not in MEAL_TYPES:
        raise HTTPException(422, "Invalid meal type")
    try:
        return MealEntryCreate(
            date=day,
            meal_type=meal_type,
            food_name=food_name.strip(),
            protein=protein,
            notes=clean_notes(notes),
        )
    except ValidationError as exc:
        raise HTTPException(422, str(exc)) from exc


def weight_data(day, weight, notes):
    try:
        return WeightEntryCreate(
            date=day,
            weight=weight,
            notes=clean_notes(notes),
        )
    except ValidationError as exc:
        raise HTTPException(422, str(exc)) from exc


@app.get("/")
def dashboard(request: Request, db: Session = Depends(get_db)):
    return render(
        request,
        "dashboard.html",
        stats=crud.dashboard_stats(db, date.today(), PROTEIN_GOAL),
        recent=crud.recent_meals(db),
        summary=crud.weekly_summary(db, date.today()),
    )


@app.get("/log")
def daily_log(
    request: Request,
    selected_date: date | None = None,
    q: str = "",
    edit_id: int | None = None,
    db: Session = Depends(get_db),
):
    selected = selected_date or date.today()
    query = q.strip()
    entries = crud.search_meals(db, query) if query else crud.meals_for_day(db, selected)
    editing = db.get(MealEntry, edit_id) if edit_id else None
    if editing:
        selected = editing.date
    return render(
        request,
        "log.html",
        entries=entries,
        selected_date=selected,
        query=query,
        editing=editing,
        meal_types=MEAL_TYPES,
        total=round(sum(entry.protein for entry in entries), 2) if not query else None,
    )


@app.post("/log")
def create_meal(
    day: date = Form(alias="date"),
    meal_type: str = Form(),
    food_name: str = Form(),
    protein: float = Form(),
    notes: str = Form(default=""),
    db: Session = Depends(get_db),
):
    crud.add_meal(db, meal_data(day, meal_type, food_name, protein, notes))
    return RedirectResponse(f"/log?selected_date={day}", status_code=303)


@app.post("/log/{entry_id}/edit")
def edit_meal(
    entry_id: int,
    day: date = Form(alias="date"),
    meal_type: str = Form(),
    food_name: str = Form(),
    protein: float = Form(),
    notes: str = Form(default=""),
    db: Session = Depends(get_db),
):
    entry = db.get(MealEntry, entry_id)
    if not entry:
        raise HTTPException(404, "Meal entry not found")
    crud.update_meal(db, entry, meal_data(day, meal_type, food_name, protein, notes))
    return RedirectResponse(f"/log?selected_date={day}", status_code=303)


@app.post("/log/{entry_id}/delete")
def delete_meal(entry_id: int, entry_date: date = Form(), db: Session = Depends(get_db)):
    crud.delete_entry(db, MealEntry, entry_id)
    return RedirectResponse(f"/log?selected_date={entry_date}", status_code=303)


@app.get("/weight")
def weight_page(
    request: Request,
    edit_id: int | None = None,
    db: Session = Depends(get_db),
):
    return render(
        request,
        "weight.html",
        entries=crud.weight_history(db),
        editing=db.get(WeightEntry, edit_id) if edit_id else None,
    )


@app.post("/weight")
def create_weight(
    day: date = Form(alias="date"),
    weight: float = Form(),
    notes: str = Form(default=""),
    db: Session = Depends(get_db),
):
    crud.add_weight(db, weight_data(day, weight, notes))
    return RedirectResponse("/weight", status_code=303)


@app.post("/weight/{entry_id}/edit")
def edit_weight(
    entry_id: int,
    day: date = Form(alias="date"),
    weight: float = Form(),
    notes: str = Form(default=""),
    db: Session = Depends(get_db),
):
    entry = db.get(WeightEntry, entry_id)
    if not entry:
        raise HTTPException(404, "Weight entry not found")
    crud.update_weight(db, entry, weight_data(day, weight, notes))
    return RedirectResponse("/weight", status_code=303)


@app.post("/weight/{entry_id}/delete")
def delete_weight(entry_id: int, db: Session = Depends(get_db)):
    crud.delete_entry(db, WeightEntry, entry_id)
    return RedirectResponse("/weight", status_code=303)


@app.get("/analytics")
def analytics(request: Request, db: Session = Depends(get_db)):
    return render(
        request,
        "analytics.html",
        charts=crud.analytics_data(db, date.today(), PROTEIN_GOAL),
    )


@app.get("/health")
def health():
    return {"status": "ok"}
