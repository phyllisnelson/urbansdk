import pandas as pd
import pytest
from sqlalchemy.orm import Session

from app.database import Link, SpeedRecord
from app.ingest import Ingester
from app.settings import settings


@pytest.fixture(scope="module")
def links_df():
    return pd.read_parquet(settings.link_info_file)


@pytest.fixture(scope="module")
def speed_df():
    return pd.read_parquet(settings.speed_data_file)


@pytest.fixture(scope="module")
def expected_link_count(links_df):
    return len(links_df)


@pytest.fixture(scope="module")
def expected_speed_record_count(speed_df):
    return len(speed_df)


@pytest.fixture(scope="module")
def real_data(engine, links_df, speed_df):
    """Load both parquet files into the DB once; clean up after the module."""
    ingester = Ingester()
    session = Session(engine)
    try:
        ingester.load_links(links_df, session)
        ingester.load_speed_records(speed_df, session)
        yield
    finally:
        session.execute(SpeedRecord.__table__.delete())
        session.execute(Link.__table__.delete())
        session.commit()
        session.close()
