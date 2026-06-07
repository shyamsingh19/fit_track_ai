from sqlalchemy import create_engine

from app.core.config import settings
from app.models.base import Base


def init_db():
    # Ensure models are imported before metadata.create_all().
    from app.models.user import User  # noqa: F401
    from app.models.food_entry import FoodEntry  # noqa: F401
    from app.models.daily_metric import DailyMetric  # noqa: F401
    from app.models.workout import Workout  # noqa: F401

    engine = create_engine(settings.database_url, pool_pre_ping=True)
    Base.metadata.create_all(bind=engine)
    return engine


