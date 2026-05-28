# This file defines database connectivity and session lifecycle management for the app

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# The engine is SQLAlchemy's connection to PostgreSQL
# create_engine reads the URL and sets up the connection pool
engine = create_engine(settings.DATABASE_URL)

# sessionmaker is a factory for creating new Session objects
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False, 
    bind=engine)

# get_db is what FastAPI endpoints will use to get a db session
def get_db():
    db = SessionLocal() # create a new session
    try:
        yield db # api endpoint uses the db here
    finally:
        db.close() # close the session when done

