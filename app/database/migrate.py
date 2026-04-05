import logging

from sqlalchemy import text

from app.database.connection import Base, engine

log = logging.getLogger(__name__)


def create_postgis_extension() -> None:
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
        conn.commit()


def migrate() -> None:
    create_postgis_extension()
    Base.metadata.create_all(bind=engine)
    log.info("Tables created.")
