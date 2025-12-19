"""
Database configuration and session management
"""
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from urllib.parse import urlparse
import logging
import os

logger = logging.getLogger(__name__)

def validate_database_url(url):
    """
    Validate that DATABASE_URL is a proper PostgreSQL URL
    """
    parsed = urlparse(url)
    if parsed.scheme != 'postgresql':
        raise ValueError("DATABASE_URL must be a PostgreSQL URL")
    if not parsed.hostname or not parsed.path.lstrip('/'):
        raise ValueError("DATABASE_URL must include hostname and database name")

# Database URL from environment variable
# Port 5433 to avoid conflict with local PostgreSQL service on port 5432
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://healthpulse:healthpulse@127.0.0.1:5433/healthpulse_db"
)

validate_database_url(DATABASE_URL)

# Create SQLAlchemy engine
try:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,  # Verify connections before using
        pool_size=10,
        max_overflow=20
    )
    # Test connection
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    logger.info("Database connection established successfully")
except Exception as e:
    logger.error(f"Failed to connect to database: {e}")
    raise

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db():
    """
    Dependency for getting database session
    Use with FastAPI Depends()
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        raise
    finally:
        db.close()

