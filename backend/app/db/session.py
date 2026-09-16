from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# SQLite needs this extra arg because it normally only allows one thread
# to use a connection; FastAPI can call the DB from different threads.
connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """FastAPI dependency: gives a route a DB session, closes it when done."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
