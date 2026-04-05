import importlib
from unittest.mock import MagicMock

from app.database import connection

migrate_module = importlib.import_module("app.database.migrate")


def test_get_db_yields_session_and_closes_it(monkeypatch):
    session = MagicMock()
    monkeypatch.setattr(connection, "SessionLocal", lambda: session)

    gen = connection.get_db()
    yielded = next(gen)
    assert yielded is session

    try:
        next(gen)
    except StopIteration:
        pass

    session.close.assert_called_once()


def test_create_postgis_extension_executes_and_commits(monkeypatch):
    conn = MagicMock()
    ctx = MagicMock()
    ctx.__enter__.return_value = conn
    ctx.__exit__.return_value = False
    fake_engine = MagicMock()
    fake_engine.connect.return_value = ctx
    monkeypatch.setattr(migrate_module, "engine", fake_engine)

    migrate_module.create_postgis_extension()

    conn.execute.assert_called_once()
    conn.commit.assert_called_once()


def test_migrate_creates_tables(monkeypatch):
    create_postgis = MagicMock()
    create_all = MagicMock()
    monkeypatch.setattr(migrate_module, "create_postgis_extension", create_postgis)
    monkeypatch.setattr(migrate_module.Base.metadata, "create_all", create_all)

    migrate_module.migrate()

    create_postgis.assert_called_once()
    create_all.assert_called_once_with(bind=migrate_module.engine)
