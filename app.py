import os
from contextlib import asynccontextmanager
from datetime import date

from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import bcrypt
from sqlalchemy import select
from sqlalchemy.orm import Session

import crud
from crud import get_ist_date
from database import Base, SessionLocal, engine, get_db
from models import DietPlan, MealEntry, User, WeightEntry
from schemas import MEAL_TYPES, MealEntryCreate, WeightEntryCreate


try:
    PROTEIN_GOAL = float(os.getenv("PROTEIN_GOAL", "120"))
    if PROTEIN_GOAL <= 0:
        raise ValueError
except ValueError as exc:
    raise RuntimeError("PROTEIN_GOAL must be a positive number") from exc


SESSION_COOKIE_NAME = "session_user_id"
SESSION_COOKIE_MAX_AGE_SECONDS = 60 * 60 * 24 * 30  # 30 days
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
IS_PRODUCTION = ENVIRONMENT == "production"



class NotAuthenticatedException(Exception):
    """Custom exception to catch unauthenticated page requests."""

    pass


def redirect_to_login(request: Request):
    return RedirectResponse(url="/login", status_code=303)


async def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    raw = request.cookies.get(SESSION_COOKIE_NAME)
    if not raw:
        raise NotAuthenticatedException()

    try:
        user_id = int(raw)
    except ValueError:
        raise NotAuthenticatedException()

    user = db.scalar(select(User).where(User.id == user_id))
    if not user:
        raise NotAuthenticatedException()

    return user


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


@app.exception_handler(NotAuthenticatedException)
async def auth_exception_handler(request: Request, exc: NotAuthenticatedException):
    """Intercepts unauthenticated exceptions and routes users to the login page."""
    resp = RedirectResponse(url="/login", status_code=303)
    # Clear any corrupted or expired cookies explicitly during redirect
    resp.delete_cookie(SESSION_COOKIE_NAME, path="/")
    return resp


def render(request: Request, template: str, **context):
    return templates.TemplateResponse(
        request=request,
        name=template,
        context={
            "goal": PROTEIN_GOAL,
            "today": get_ist_date(),
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
    except Exception as exc:
        raise HTTPException(422, str(exc)) from exc


def weight_data(day, weight, notes):
    try:
        return WeightEntryCreate(
            date=day,
            weight=weight,
            notes=clean_notes(notes),
        )
    except Exception as exc:
        raise HTTPException(422, str(exc)) from exc


@app.get("/")
def dashboard(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return render(
        request,
        "dashboard.html",
        stats=crud.dashboard_stats(db, current_user.id, get_ist_date(), PROTEIN_GOAL),
        recent=crud.recent_meals(db, current_user.id),
        summary=crud.weekly_summary(db, current_user.id, get_ist_date()),
    )


@app.get("/log")
def daily_log(
    request: Request,
    selected_date: date | None = None,
    q: str = "",
    edit_id: int | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    selected = selected_date or get_ist_date()
    query = q.strip()

    entries = (
        crud.search_meals(db, current_user.id, query)
        if query
        else crud.meals_for_day(db, current_user.id, selected)
    )

    editing = None
    if edit_id:
        editing = db.scalar(
            select(MealEntry).where(
                MealEntry.id == edit_id, MealEntry.user_id == current_user.id
            )
        )
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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    crud.add_meal(
        db, current_user.id, meal_data(day, meal_type, food_name, protein, notes)
    )
    return RedirectResponse(f"/log?selected_date={day}", status_code=303)


@app.post("/log/{entry_id}/edit")
def edit_meal(
    entry_id: int,
    day: date = Form(alias="date"),
    meal_type: str = Form(),
    food_name: str = Form(),
    protein: float = Form(),
    notes: str = Form(default=""),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    updated = crud.update_meal(
        db,
        current_user.id,
        entry_id,
        meal_data(day, meal_type, food_name, protein, notes),
    )
    if not updated:
        raise HTTPException(404, "Meal entry not found")
    return RedirectResponse(f"/log?selected_date={day}", status_code=303)


@app.post("/log/{entry_id}/delete")
def delete_meal(
    entry_id: int,
    entry_date: date = Form(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ok = crud.delete_entry(db, current_user.id, MealEntry, entry_id)
    if not ok:
        raise HTTPException(404, "Meal entry not found")
    return RedirectResponse(f"/log?selected_date={entry_date}", status_code=303)


@app.get("/weight")
def weight_page(
    request: Request,
    edit_id: int | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    editing = None
    if edit_id:
        editing = db.scalar(
            select(WeightEntry).where(
                WeightEntry.id == edit_id,
                WeightEntry.user_id == current_user.id,
            )
        )

    return render(
        request,
        "weight.html",
        entries=crud.weight_history(db, current_user.id),
        editing=editing,
    )


@app.post("/weight")
def create_weight(
    day: date = Form(alias="date"),
    weight: float = Form(),
    notes: str = Form(default=""),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    crud.add_weight(db, current_user.id, weight_data(day, weight, notes))
    return RedirectResponse("/weight", status_code=303)


@app.post("/weight/{entry_id}/edit")
def edit_weight(
    entry_id: int,
    day: date = Form(alias="date"),
    weight: float = Form(),
    notes: str = Form(default=""),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    updated = crud.update_weight(
        db,
        current_user.id,
        entry_id,
        weight_data(day, weight, notes),
    )
    if not updated:
        raise HTTPException(404, "Weight entry not found")
    return RedirectResponse("/weight", status_code=303)


@app.post("/weight/{entry_id}/delete")
def delete_weight(
    entry_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ok = crud.delete_entry(db, current_user.id, WeightEntry, entry_id)
    if not ok:
        raise HTTPException(404, "Weight entry not found")
    return RedirectResponse("/weight", status_code=303)


@app.get("/diet-chart")
def diet_chart(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Fetch all diet plan items for the current authenticated user
    plans = db.scalars(
        select(DietPlan)
        .where(DietPlan.user_id == current_user.id)
        .order_by(DietPlan.day_of_week, DietPlan.meal_type, DietPlan.id)
    ).all()

    # Group by day_of_week into a dict ordered Monday -> Sunday
    day_order = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]
    grouped_plans = {day: [] for day in day_order}

    for item in plans:
        if item.day_of_week in grouped_plans:
            grouped_plans[item.day_of_week].append(item)

    for day in day_order:
        grouped_plans[day].sort(key=lambda x: (x.meal_type or "", x.id))

    total = round(sum(p.target_protein for p in plans), 2)

    return render(
        request,
        "diet_chart.html",
        grouped_plans=grouped_plans,
        day_order=day_order,
        total_target_protein=total,
    )




@app.post("/diet-chart/add")
def add_diet_plan(
    meal_type: str = Form(),
    target_food: str = Form(),
    target_protein: float = Form(),
    notes: str = Form(default=""),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    crud.create_diet_plan(
        db,
        meal_type=meal_type,
        target_food=target_food,
        target_protein=target_protein,
        notes=notes if notes.strip() else None,
    )
    return RedirectResponse(url="/diet-chart", status_code=303)


@app.post("/diet-chart/delete/{plan_id}")
def delete_diet_plan_route(
    plan_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    crud.delete_diet_plan(db, plan_id)
    return RedirectResponse(url="/diet-chart", status_code=303)


@app.get("/analytics")
def analytics(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return render(
        request,
        "analytics.html",
        charts=crud.analytics_data(db, current_user.id, get_ist_date(), PROTEIN_GOAL),
    )


@app.get("/login")
def login_page(request: Request):

    return templates.TemplateResponse(
        request=request, name="login.html", context={"error": None}
    )


@app.post("/register")
def register(
    request: Request,
    username: str = Form(),
    password: str = Form(),
    db: Session = Depends(get_db),
):
    username = username.strip()
    if not username:
        return render(request, "login.html", error="Username is required.")

    if not password or len(password) < 8:
        return render(
            request, "login.html", error="Password must be at least 8 characters."
        )

    exists = db.scalar(select(User).where(User.username == username))
    if exists:
        return render(request, "login.html", error="Username already exists.")

    hashed_bytes = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    user = User(username=username, hashed_password=hashed_bytes.decode('utf-8'))
    db.add(user)
    db.commit()
    db.refresh(user)

    resp = RedirectResponse(url="/", status_code=303)
    resp.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=str(user.id),
        httponly=True,
        secure=IS_PRODUCTION,
        samesite="lax",
        max_age=SESSION_COOKIE_MAX_AGE_SECONDS,
        path="/",
    )
    return resp


@app.post("/login")
def login(
    request: Request,
    username: str = Form(),
    password: str = Form(),
    db: Session = Depends(get_db),
):
    username = username.strip()
    user = db.scalar(select(User).where(User.username == username))
    password_matches = bcrypt.checkpw(password.encode('utf-8'), user.hashed_password.encode('utf-8'))
    if not user or not password_matches:
        return render(request, "login.html", error="Invalid username or password.")

    resp = RedirectResponse(url="/", status_code=303)
    resp.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=str(user.id),
        httponly=True,
        secure=IS_PRODUCTION,
        samesite="lax",
        max_age=SESSION_COOKIE_MAX_AGE_SECONDS,
        path="/",
    )
    return resp


@app.post("/logout")
def logout():
    resp = RedirectResponse(url="/login", status_code=303)
    resp.delete_cookie(SESSION_COOKIE_NAME, path="/")
    return resp


@app.get("/health")
def health():
    return {"status": "ok"}
