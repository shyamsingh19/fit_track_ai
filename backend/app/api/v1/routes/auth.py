from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt
from app.utils.passwords import hash_password, verify_password

from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import TokenResponse, TokenPair


# NOTE: JWT auth dependency will be added when we implement protected routes (/me, food logs, etc.)


router = APIRouter()




class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str



def _hash_password(password: str) -> str:
    return hash_password(password)



def get_current_user_id(token: str):
    """Return the authenticated user's id as a uuid.UUID."""
    import uuid

    payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_alg])
    if payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject")

    return uuid.UUID(str(user_id))




def _verify_password(password: str, password_hash: str) -> bool:
    return verify_password(password, password_hash)



def _create_token_pair(user_id: str) -> TokenPair:
    now = datetime.now(timezone.utc)
    access_exp = now + timedelta(minutes=settings.access_token_expires_minutes)
    refresh_exp = now + timedelta(days=settings.refresh_token_expires_days)

    access_token = jwt.encode(
        {"sub": user_id, "type": "access", "exp": access_exp},
        settings.jwt_secret,
        algorithm=settings.jwt_alg,
    )
    refresh_token = jwt.encode(
        {"sub": user_id, "type": "refresh", "exp": refresh_exp},
        settings.jwt_secret,
        algorithm=settings.jwt_alg,
    )
    return TokenPair(access_token=access_token, refresh_token=refresh_token)


@router.post("/register", response_model=TokenResponse)
def register(req: RegisterRequest, db: Session = Depends(get_db)) -> TokenResponse:
    existing = db.query(User).filter(User.email == req.email.lower().strip()).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(
        full_name=req.name,
        email=req.email.lower().strip(),
        hashed_password=_hash_password(req.password),
    )


    db.add(user)
    db.commit()
    db.refresh(user)

    tokens = _create_token_pair(str(user.id))
    return TokenResponse(**tokens.model_dump())


@router.post("/login", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)) -> TokenResponse:
    user = db.query(User).filter(User.email == form_data.username.lower().strip()).first()
    if not user or not _verify_password(form_data.password, user.hashed_password):

        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    tokens = _create_token_pair(str(user.id))
    return TokenResponse(**tokens.model_dump())


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/refresh", response_model=TokenResponse)
def refresh(req: RefreshRequest) -> TokenResponse:
    try:
        payload = jwt.decode(req.refresh_token, settings.jwt_secret, algorithms=[settings.jwt_alg])
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject")

    tokens = _create_token_pair(user_id)
    return TokenResponse(**tokens.model_dump())

