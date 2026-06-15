"""
Shared test fixtures.

Every test runs against a real Postgres connection wrapped in a single
transaction that is rolled back at the end, so tests never persist anything
to the database.

"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.session import engine, get_db
from main import app


@pytest.fixture
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def client(db_session):
    """A TestClient whose endpoints use the rolled-back test session."""

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
