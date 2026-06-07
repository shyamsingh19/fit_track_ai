import uuid

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    created_at: Mapped[str] = mapped_column(nullable=False, server_default="now()")

    updated_at: Mapped[str] = mapped_column(nullable=False, server_default="now()")



