from database import Base, SessionLocal, engine
from crud import seed_sample_data


if __name__ == "__main__":
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        created = seed_sample_data(db)
    print("Sample data added." if created else "Database already contains meal data.")
