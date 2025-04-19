import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Database URL from environment or default to local SQLite file
DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./photos.db")

# Engine creation; SQLite needs check_same_thread
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Session factory for DB sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for ORM models
Base = declarative_base()
