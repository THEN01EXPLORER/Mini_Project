"""
Database configuration for user authentication.

Using SQLite for simplicity - easy to set up, no external dependencies.
For production, switch to PostgreSQL with async driver.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# SQLite database file in project root
DATABASE_URL = "sqlite:///./users.db"

# Create engine - check_same_thread=False needed for SQLite + FastAPI
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # SQLite specific
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db():
    """
    Dependency that provides a database session.
    
    Usage:
        @app.get("/users")
        def get_users(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables. Called on app startup."""
    Base.metadata.create_all(bind=engine)
