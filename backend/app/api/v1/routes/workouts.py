from datetime import date

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.api.v1.routes.auth import get_current_user_id
from app.db.session import get_db
from app.models.workout import Workout
from app.schemas.workouts import WorkoutHistoryItem, WorkoutLogRequest

router = APIRouter()


@router.post("", response_model=WorkoutLogRequest)
def log_workout(req: WorkoutLogRequest, authorization: str | None = Header(default=None), db: Session = Depends(get_db)) -> WorkoutLogRequest:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1]
    user_id = get_current_user_id(token)

    d = req.date.isoformat() if req.date else date.today().isoformat()

    row = Workout(
        user_id=user_id,
        date=d,
        workout_type=req.workout_type,
        duration_minutes=req.duration_minutes,
        notes=req.notes,
    )
    db.add(row)
    db.commit()
    return req


@router.get("", response_model=list[WorkoutHistoryItem])
def workouts_history(authorization: str | None = Header(default=None), db: Session = Depends(get_db)) -> list[WorkoutHistoryItem]:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1]
    user_id = get_current_user_id(token)

    rows = db.query(Workout).filter(Workout.user_id == user_id).order_by(Workout.date.asc()).all()
    out: list[WorkoutHistoryItem] = []
    for r in rows:
        out.append(
            WorkoutHistoryItem(
                date=date.fromisoformat(r.date),
                workout_type=r.workout_type,
                duration_minutes=r.duration_minutes,
                notes=r.notes,
            )
        )
    return out


