import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.app.core.config import settings
from backend.app.core.logging import logger

connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def init_db():
    """Initializes the database schema."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully at %s", settings.DATABASE_URL)
    except Exception as e:
        logger.error("Failed to initialize database: %s", str(e))
        raise

def get_db():
    """Dependency for providing database sessions to FastAPI endpoints."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
