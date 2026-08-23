import logging
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

from vigil.config import get_settings
from vigil.core.exceptions import DatabasePersistenceError

logger = logging.getLogger(__name__)

_engine = None
_SessionFactory = None

def get_engine():
    """
    Initializes and returns the singleton SQLAlchemy engine.
    """
    global _engine
    if _engine is None:
        settings = get_settings()
        db_url = str(settings.DATABASE_URL)
        try:
            # Configure connection pool parameters
            _engine = create_engine(
                db_url,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True
            )
        except Exception as e:
            raise DatabasePersistenceError(f"Failed to initialize SQLAlchemy engine: {e}")
    return _engine

def get_session_factory():
    """
    Initializes and returns the singleton SQLAlchemy sessionmaker.
    """
    global _SessionFactory
    if _SessionFactory is None:
        engine = get_engine()
        _SessionFactory = sessionmaker(bind=engine)
    return _SessionFactory

@contextmanager
def get_session() -> Session:
    """
    Context manager providing a database session.
    Commits on success, rolls back on exception, and guarantees session close.
    Maps all DB exceptions to DatabasePersistenceError.
    """
    factory = get_session_factory()
    session = factory()
    try:
        yield session
        session.commit()
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Database operation failed, rolled back: {e}")
        raise DatabasePersistenceError(f"Database error occurred: {e}")
    except Exception as e:
        session.rollback()
        logger.error(f"Unexpected database exception, rolled back: {e}")
        raise DatabasePersistenceError(f"Unexpected database error: {e}")
    finally:
        session.close()
