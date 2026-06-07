from datetime import date

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.api.v1.routes.auth import get_current_user_id
from app.db.session import get_db
from app.models.daily_metric import DailyMetric
from app.schemas.weights import WeightHistoryItem, WeightLogRequest

router = APIRouter()


@router.post("", response_model=WeightLogRequest)
def log_weight(req: WeightLogRequest, authorization: str | None = Header(default=None), db: Session = Depends(get_db)) -> WeightLogRequest:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1]
    user_id = get_current_user_id(token)

    d = req.date.isoformat() if req.date else date.today().isoformat()

    row = db.query(DailyMetric).filter(DailyMetric.user_id == user_id, DailyMetric.date == d).first()
    if not row:
        row = DailyMetric(user_id=user_id, date=d)
        db.add(row)

    row.weight = req.weight
    db.commit()
    return req


@router.get("/history", response_model=list[WeightHistoryItem])
def weight_history(authorization: str | None = Header(default=None), db: Session = Depends(get_db)) -> list[WeightHistoryItem]:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1]
    user_id = get_current_user_id(token)

    rows = db.query(DailyMetric).filter(DailyMetric.user_id == user_id).filter(DailyMetric.weight.isnot(None)).order_by(DailyMetric.date.asc()).all()
    out: list[WeightHistoryItem] = []
    for r in rows:
        out.append(WeightHistoryItem(date=date.fromisoformat(r.date), weight=r.weight))
    return out


