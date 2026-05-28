# This file defines the Base class that all our SQLAlchemy models will inherit from. 
# Alembic will use Base.metadata to look for tables to create

from sqlalchemy.orm import DeclarativeBase # the sqlalchemy system for defining models

# All models will do class Dataset(Base) to register them with sqlalchemy 

class Base(DeclarativeBase):
    pass

