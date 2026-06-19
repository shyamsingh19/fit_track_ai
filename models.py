from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, String, Text

from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(150), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(Text)

    meals: Mapped[list[MealEntry]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    weights: Mapped[list[WeightEntry]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


class MealEntry(Base):
    __tablename__ = "meal_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )

    date: Mapped[date] = mapped_column(Date, index=True)
    meal_type: Mapped[str] = mapped_column(String(30))
    food_name: Mapped[str] = mapped_column(String(250), index=True)
    protein: Mapped[float] = mapped_column(Float)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped[User] = relationship(back_populates="meals")


class WeightEntry(Base):
    __tablename__ = "weight_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )

    date: Mapped[date] = mapped_column(Date, index=True)
    weight: Mapped[float] = mapped_column(Float)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped[User] = relationship(back_populates="weights")


class DietPlan(Base):
    __tablename__ = "diet_plans"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    day_of_week: Mapped[str] = mapped_column(String(20), index=True)  # e.g., 'Monday'
    meal_type: Mapped[str] = mapped_column(String(50))  # e.g., 'Pre-Workout'
    target_food: Mapped[str] = mapped_column(String(500))
    target_protein: Mapped[float] = mapped_column(Float)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)



