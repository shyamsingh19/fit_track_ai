from fastapi import APIRouter

from app.api.v1.routes import auth, dashboard, foods, workouts, weights

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(foods.router, prefix="/foods", tags=["foods"])
api_router.include_router(weights.router, prefix="/weights", tags=["weights"])
api_router.include_router(workouts.router, prefix="/workouts", tags=["workouts"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])



