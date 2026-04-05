import os
from datetime import datetime, timezone

import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

load_dotenv()

from app.database import Base, get_db
from app.main import app
from tests.factories import LinkFactory, SpeedRecordFactory

# Shared test timestamps (UTC)
MON_AM = datetime(2024, 1, 1, 8, 30, tzinfo=timezone.utc)
MON_PM = datetime(2024, 1, 1, 17, 0, tzinfo=timezone.utc)
TUE_AM = datetime(2024, 1, 2, 8, 30, tzinfo=timezone.utc)
WED_AM = datetime(2024, 1, 3, 8, 30, tzinfo=timezone.utc)
THU_AM = datetime(2024, 1, 4, 8, 30, tzinfo=timezone.utc)

DATABASE_URL = os.environ["DATABASE_URL"]


@pytest.fixture(scope="session")
def engine():
    eng = create_engine(DATABASE_URL)
    with eng.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
        conn.commit()
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)


@pytest.fixture
def db(engine):
    """Each test runs in a transaction that is rolled back on teardown."""
    with engine.connect() as connection:
        transaction = connection.begin()
        session = Session(connection, join_transaction_mode="create_savepoint")
        LinkFactory._meta.sqlalchemy_session = session
        SpeedRecordFactory._meta.sqlalchemy_session = session
        yield session
        session.close()
        transaction.rollback()


@pytest.fixture
def client(db):
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
