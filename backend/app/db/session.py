from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

# 1. Create the SQLAlchemy Database Engine
# pool_pre_ping=True checks connections before using them, preventing stale connection errors
# pool_recycle=3600 recycles connections after 1 hour (common for MySQL server timeouts)
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600
)

# 2. Create the SessionLocal class
# Each instance of SessionLocal will be a single database session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 3. Base class for all SQLAlchemy ORM models to inherit from
Base = declarative_base()


def get_db():
    """
    FastAPI Dependency:
    Yields a database session per HTTP request and ensures it is cleanly closed
    when the request completes, even if an unhandled error occurs.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
